import asyncio
import logging
import logging.config
import dialogs

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from aiogram_dialog import setup_dialogs

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncEngine
)

from logging_setting import logging_config
from config import load_config, Config
from middleware import DbSessionMiddleware, LoggingMiddleware
from db import Base


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
        url=f'postgresql+psycopg://'
        f'{config.data_base.NAME}:{config.data_base.PASSWORD}@'
        f'{config.data_base.HOST}/fitness',
        echo=False
    )

    await create_tables(engine=engine)

    Session = async_sessionmaker(engine, expire_on_commit=False)

    bot = Bot(
        token=config.tg_bot.TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    dp.update.middleware(DbSessionMiddleware(Session))

    router: Router = dialogs.setup_all_dialogs(Router)
    router.callback_query.middleware(LoggingMiddleware())
    router.message.middleware(LoggingMiddleware())

    dp.include_routers(router)
    setup_dialogs(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

    logger.info('start polling')

if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy()) #  Убрать при деплое
    asyncio.run(main())
