import logging

from pprint import pprint
from aiogram_dialog import DialogManager


async def get_data(dialog_manager: DialogManager, **kwargs):

    dialog_manager.dialog_data.update(dialog_manager.start_data)

    return dialog_manager.dialog_data


async def get_workout(dialog_manager: DialogManager, **kwargs):

    return dialog_manager.dialog_data
