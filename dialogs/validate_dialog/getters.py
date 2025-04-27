import logging

from aiogram_dialog import DialogManager

logger = logging.getLogger(__name__)


async def get_data(dialog_manager: DialogManager, **kwargs):

    return dialog_manager.start_data
