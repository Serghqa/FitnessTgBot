from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import load_config, Config


config: Config = load_config()

bot = Bot(
    token=config.tg_bot.TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
