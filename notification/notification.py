import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramBadRequest


logger = logging.getLogger(__name__)


async def send_notification(
    bot: Bot,
    user_id: int,
    text: str
) -> None:
    """
    Отправляет текстовое сообщение пользователю через Telegram-бота.
    """

    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
        )
        logger.info(
            'Сообщение пользователю user_id=%s, успешно отправленно.',
            user_id,
        )

    except (TelegramForbiddenError, TelegramBadRequest) as error:
        logger.warning(
            'Ошибка, сообщение пользователю user_id=%s не удалось отправить.',
            user_id,
            exc_info=error,
        )
