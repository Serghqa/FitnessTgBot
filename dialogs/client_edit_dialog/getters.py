import logging

from aiogram_dialog import DialogManager
from typing import Any


logger = logging.getLogger(__name__)


async def get_data(
    dialog_manager: DialogManager,
    **kwargs
) -> dict[str, Any]:

    return dialog_manager.start_data
