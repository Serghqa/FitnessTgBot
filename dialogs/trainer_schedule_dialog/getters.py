import logging

from aiogram_dialog import DialogManager


logger = logging.getLogger(__name__)


async def selection_getter(dialog_manager: DialogManager, **kwargs):

    selected = dialog_manager.dialog_data.get('selected_dates', [])

    return {
        'selected': ', '.join(sorted(selected)),
    }


async def get_multiselect_data(dialog_manager: DialogManager, **kwargs):

    return {
        'rows1': [(str(i), (str(i))) for i in range(6)],
        'rows2': [(str(i), (str(i))) for i in range(6, 12)],
        'rows3': [(str(i), (str(i))) for i in range(12, 18)],
        'rows4': [(str(i), (str(i))) for i in range(18, 24)]
    }
