import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError

from aiogram_dialog import DialogManager


logger = logging.getLogger(__name__)


async def send_message(
    dialog_manager: DialogManager,
    user_id: int,
    text: str
):

    bot: Bot = dialog_manager.event.bot

    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
        )
    except TelegramForbiddenError as error:
        logger.warning(error)
