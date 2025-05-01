import logging

from aiogram_dialog import DialogManager 


async def selection_getter(dialog_manager: DialogManager, **kwargs):

    selected = dialog_manager.dialog_data.get('selected_dates', [])

    return {
        'selected': ', '.join(sorted(selected)),
    }