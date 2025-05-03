import asyncio
import logging
import logging.config
import dialogs

from aiogram import Bot, Dispatcher, Router
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from aiogram_dialog import setup_dialogs

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from logging_setting import logging_config
from config import load_config, Config
from middleware import DbSessionMiddleware
from db import Base


async def main():

    logging.config.dictConfig(logging_config)

    config: Config = load_config()

    engine = create_engine(url='sqlite:///Fitness.db', echo=False)

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    Session = sessionmaker(engine, expire_on_commit=False)

    bot = Bot(token=config.tg_bot.TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()

    dp.update.middleware(DbSessionMiddleware(Session))

    dp.include_routers(dialogs.setup_all_dialogs(Router))
    setup_dialogs(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
