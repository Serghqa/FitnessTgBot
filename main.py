import asyncio
import dialogs
import logging
import logging.config

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.types import BotCommand
from aiogram_dialog import setup_dialogs
from logging import Logger
from middleware import DbSessionMiddleware, LoggingMiddleware
from redis.asyncio import Redis
from taskiq_broker import broker, schedule_source, scheduler
from taskiq_redis import RedisScheduleSource
from taskiq.scheduler.scheduled_task import ScheduledTask

from common import bot, engine, create_tables, Session
from logging_setting import logging_config


def setting_logging(config: dict) -> Logger:

    logging.config.dictConfig(config)
    logging.getLogger('aiogram.event').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    logger = logging.getLogger(__name__)

    return logger


logger: Logger = setting_logging(logging_config)


async def set_bot_commands(bot: Bot):

    commands = [
        BotCommand(
            command='/start',
            description='Перезапустить бота',
        ),
        BotCommand(
            command='/update',
            description='Обновить',
        )
    ]

    await bot.set_my_commands(commands)


async def set_delete_old_data(source: RedisScheduleSource) -> None:

    scheduled_tasks: list[ScheduledTask] = await source.get_schedules()

    for scheduled_task in scheduled_tasks:
        if scheduled_task.task_name == 'clear_old_data':
            await source.delete_schedule(scheduled_task.schedule_id)
            logger.info(
                'Задача очистки %s данных отменена', scheduled_task.task_name
            )

    cron = '0 3 * * 0'

    await schedule_source.add_schedule(
        ScheduledTask(
            task_name='clear_old_data',
            labels={},
            args=[],
            kwargs={},
            schedule_id='clear_old_data_id',
            cron=cron,
        )
    )
    logger.info('Периодическая очистка данных настроена на %s', cron)


def setting_dispatcher(dispatcher: Dispatcher) -> None:

    dispatcher.update.middleware(DbSessionMiddleware(Session))

    router: Router = dialogs.setup_all_dialogs(Router)
    router.callback_query.middleware(LoggingMiddleware())
    router.message.middleware(LoggingMiddleware())

    dispatcher.include_routers(router)
    setup_dialogs(dispatcher)


redis = Redis(
    host='redis',
    port=6379,
    db=0,
    socket_connect_timeout=3
)
storage = RedisStorage(
    redis=redis,
    key_builder=DefaultKeyBuilder(with_destiny=True)
)
dp = Dispatcher(storage=storage)
setting_dispatcher(dispatcher=dp)


async def main():

    await broker.startup()
    logger.info('Брокер запущен')

    await create_tables(engine=engine)
    logger.info('База данных готова к работе')

    await set_delete_old_data(schedule_source)

    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)

    await dp.start_polling(bot)
    logger.info('Бот остановлен')

    await scheduler.shutdown()
    logger.info('Планировщик остановлен')
    await broker.shutdown()
    logger.info('Брокер остановлен')


if __name__ == '__main__':
    asyncio.run(main())
