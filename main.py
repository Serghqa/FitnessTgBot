import asyncio
import dialogs
import logging
import logging.config

from aiogram import Bot, Dispatcher, Router
from aiogram.types import BotCommand
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from aiogram_dialog import setup_dialogs

from logging_setting import logging_config

from nats.js.api import StreamConfig

from nats_manager import NatsManager

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)

from config import load_config, Config
from db import Base
from middleware import DbSessionMiddleware, LoggingMiddleware


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

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)


async def main():

    logging.config.dictConfig(logging_config)
    logging.getLogger('aiogram.event').setLevel(logging.WARNING)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

    logger = logging.getLogger(__name__)

    config: Config = load_config()

    engine: AsyncEngine = create_async_engine(
        url=(
            f'postgresql+psycopg://'
            f'{config.data_base.NAME}:{config.data_base.PASSWORD}@'
            f'{config.data_base.HOST}/fitness'
        ),
        echo=False,
    )

    await create_tables(engine=engine)

    Session = async_sessionmaker(engine, expire_on_commit=False)

    bot = Bot(
        token=config.tg_bot.TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    nats_manager = NatsManager(bot, config.nats.servers)
    stream_config = StreamConfig(
        name=config.nats_consumer.stream_name,
        subjects=[config.nats_consumer.subject_name],
        #storage='file',
    )
    nc, js = await nats_manager.connect(stream_config)

    dp = Dispatcher()

    dp.update.middleware(DbSessionMiddleware(Session))

    router: Router = dialogs.setup_all_dialogs(Router)
    router.callback_query.middleware(LoggingMiddleware())
    router.message.middleware(LoggingMiddleware())

    dp.include_routers(router)
    setup_dialogs(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    await set_bot_commands(bot)

    try:
        await asyncio.gather(
            dp.start_polling(bot, nats_manager=nats_manager),
            nats_manager.subscribe_to_notifications(
                durable=config.nats_consumer.durable_name,
                subject=config.nats_consumer.subject_name,
                stream=config.nats_consumer.stream_name,
            ),
        )
    except Exception as error:
        logger.warning(error)
    finally:
        await nc.close()

    #  await dp.start_polling(bot)

    logger.info('start polling')

if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) #  Убрать при деплое
    asyncio.run(main())
