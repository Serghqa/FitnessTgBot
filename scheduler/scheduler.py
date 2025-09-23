import logging

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from datetime import datetime, timezone, timedelta

from sqlalchemy import delete, and_, select

logger = logging.getLogger(__name__)


class SchedulerManager:

    def __init__(self):

        self.scheduler = AsyncIOScheduler()

    async def perform_cleanup(self):

        """Выполнение всей процедуры очистки"""

        logger.info("Запуск очистки устаревших данных")

        start_time = datetime.now(timezone.utc)

        # Выполняем все операции очистки
        messages_deleted = await self.delete_old_messages()
        actions_deleted = await self.delete_old_user_actions()
        users_deleted = await self.delete_inactive_users()

        end_time = datetime.now(timezone.utc)
        duration = (end_time - start_time).total_seconds()

        # Отправляем уведомление администратору
        if config.ADMIN_ID and self.bot:
            try:
                message = (
                    f"✅ Очистка данных завершена\n"
                    f"⏱ Время выполнения: {duration:.2f} сек\n"
                    f"🗑 Удалено:\n"
                    f"   • Сообщений: {messages_deleted}\n"
                    f"   • Действий: {actions_deleted}\n"
                    f"   • Пользователей: {users_deleted}"
                )
                await self.bot.send_message(config.ADMIN_ID, message)
            except Exception as e:
                logger.error(f"Ошибка при отправке уведомления администратору: {e}")

        logger.info(
            f"Очистка завершена за {duration:.2f} секунд. "
            f"Удалено: {messages_deleted} сообщений, "
            f"{actions_deleted} действий, "
            f"{users_deleted} пользователей"
        )

    def setup_scheduler(self):

        """Настройка планировщика"""

        # Парсим время очистки из конфига
        cleanup_time = config.CLEANUP_TIME.split(":")
        hour, minute = int(cleanup_time[0]), int(cleanup_time[1])

        # Добавляем задачу на ежедневное выполнение
        self.scheduler.add_job(
            self.perform_cleanup,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_cleanup",
            name="Ежедневная очистка устаревших данных",
            replace_existing=True
        )

        # Добавляем задачу на еженедельную статистику (по понедельникам в 10:00)
        self.scheduler.add_job(
            self.send_weekly_stats,
            trigger=CronTrigger(day_of_week=0, hour=10, minute=0),
            id="weekly_stats",
            name="Еженедельная статистика",
            replace_existing=True
        )

        logger.info(f"Планировщик настроен на очистку в {hour:02d}:{minute:02d} UTC")

    def start(self):

        """Запуск планировщика"""

        self.scheduler.start()
        logger.info("Планировщик задач запущен")

    def shutdown(self):

        """Остановка планировщика"""

        self.scheduler.shutdown()
        logger.info("Планировщик задач остановлен")
