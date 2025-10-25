import asyncio
import dialogs
import logging
import logging.config

from aiogram import Bot, Dispatcher, Router
from aiogram.fsm.storage.redis import RedisStorage, DefaultKeyBuilder
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from aiogram_dialog import setup_dialogs

from logging import Logger

from redis.asyncio import Redis

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)

from taskiq_redis import RedisScheduleSource

from taskiq.scheduler.scheduled_task import ScheduledTask

from config import load_config, Config
from db import Base
from logging_setting import logging_config
from middleware import DbSessionMiddleware, LoggingMiddleware
from taskiq_broker import broker, schedule_source
from tasks import clear_old_data


def setting_logging(config: dict) -> Logger:

    logging.config.dictConfig(config)
    logging.getLogger('aiogram.event').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    logger = logging.getLogger(__name__)
    logger.info('Настройка логов завершена')

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


async def create_tables(engine: AsyncEngine):

    logger.info('Запуск процесса создания таблиц базы данных')

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

        logger.info('Таблицы успешно созданны')


async def set_delete_old_data(source: RedisScheduleSource) -> None:

    scheduled_tasks: list[ScheduledTask] = await source.get_schedules()

    for scheduled_task in scheduled_tasks:
        if scheduled_task.task_name == clear_old_data.task_name:
            await source.delete_schedule(scheduled_task.schedule_id)
            logger.info('Задача очистки данных отменена')

    await schedule_source.add_schedule(
        ScheduledTask(
            task_name=clear_old_data.task_name,
            labels={},
            args=[],
            kwargs={},
            schedule_id=f'{clear_old_data.task_name}_id',
            cron='0 3 1 * 6',  # каждый месяц 1 числа в воскресенье в 3:00
            # cron='3 15 * * *',
        )
    )
    logger.info('Периодическая очистка данных настроена')


def create_engine(config: Config) -> AsyncEngine:

    engine: AsyncEngine = create_async_engine(
        url=(
            f'postgresql+asyncpg://'
            f'{config.data_base.NAME}:{config.data_base.PASSWORD}@'
            f'{config.data_base.HOST}/fitness'
        ),
        echo=False,
    )

    logger.info('Движок AsyncEngine успешно создан')

    return engine


def create_async_sessionmaker(engine: AsyncEngine) -> async_sessionmaker:

    logger.info('AsyncSession получен')

    return async_sessionmaker(engine, expire_on_commit=False)


def setting_dispatcher(dispatcher: Dispatcher) -> None:

    dispatcher.update.middleware(DbSessionMiddleware(Session))

    router: Router = dialogs.setup_all_dialogs(Router)
    router.callback_query.middleware(LoggingMiddleware())
    router.message.middleware(LoggingMiddleware())

    dispatcher.include_routers(router)
    setup_dialogs(dispatcher)

    logger.info('Dispatcher успешно настроен')


config: Config = load_config()
engine: AsyncEngine = create_engine(config)
Session = create_async_sessionmaker(engine)
broker.add_dependency_context({'session': Session})

redis = Redis(host='localhost')
storage = RedisStorage(
    redis=redis,
    key_builder=DefaultKeyBuilder(with_destiny=True)
)
dp = Dispatcher(storage=storage)
setting_dispatcher(dispatcher=dp)

bot = Bot(
    token=config.tg_bot.TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)


@dp.startup()
async def setup_taskiq():
    if not broker.is_worker_process:
        logger.info('Настройка taskiq завершена')
        await broker.startup()


@dp.shutdown()
async def shutdown_taskiq():
    if not broker.is_worker_process:
        logger.info('Завершение работы taskiq')
        await broker.shutdown()


async def main():

    await create_tables(engine=engine)
    await set_delete_old_data(schedule_source)

    await set_bot_commands(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

    logger.info('start polling')


if __name__ == '__main__':
    asyncio.run(main())

    # taskiq worker taskiq_broker.broker:broker -fsd
    # taskiq scheduler taskiq_broker.broker:scheduler -fsd
