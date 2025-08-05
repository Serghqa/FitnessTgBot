import logging

from typing import Callable, Awaitable, Dict, Any

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities.context import Context


logger = logging.getLogger(__name__)

class LoggingMiddleware(BaseMiddleware):

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:

        dialog_manager: DialogManager = data.get('dialog_manager')

        result = await handler(event, data)

        if dialog_manager:
            context: Context = dialog_manager.current_context()

            logger.info(
                '<<Context>>\nstart_data=%s,\ndialog_data=%s,\nstate=%s,\nwidget_data=%s\n',
                context.start_data,
                context.dialog_data,
                context.state,
                context.widget_data
            )

        return result
