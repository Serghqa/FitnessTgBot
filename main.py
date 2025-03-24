import asyncio
import logging
import logging.config

from aiogram import Bot, Dispatcher
from aiogram_dialog import setup_dialogs
from dialogs import router, start_dialog, tariner_dialog, client_dialog
from logging_setting import logging_config
from config import load_config, Config


async def main():
    logging.config.dictConfig(logging_config)

    config: Config = load_config()

    bot = Bot(token=config.tg_bot.TOKEN)
    dp = Dispatcher()
    dp.include_routers(
        router,
        start_dialog,
        tariner_dialog,
        client_dialog
    )
    setup_dialogs(dp)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
