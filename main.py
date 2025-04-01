import asyncio
import logging
import logging.config
import dialogs

from aiogram import Bot, Dispatcher, Router
from aiogram_dialog import setup_dialogs
from logging_setting import logging_config
from config import load_config, Config


async def main():
    logging.config.dictConfig(logging_config)

    config: Config = load_config()

    bot = Bot(token=config.tg_bot.TOKEN)
    dp = Dispatcher()
    dp.include_routers(dialogs.setup_all_dialogs(Router))
    setup_dialogs(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
