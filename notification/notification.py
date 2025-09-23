import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError


logger = logging.getLogger(__name__)


async def send_notification(
    bot: Bot,
    user_id: int,
    text: str
):

    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
        )
        logger.info('Сообщение пользователю успешно отправленно.')

    except TelegramForbiddenError as error:
        logger.warning('Ошибка, сообщение не удалось отправить. %s', error)
