import logging

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd.select import ManagedMultiselect
from aiogram_dialog.api.entities import Context

from db import Trainer, get_user


logger = logging.getLogger(__name__)


RADIO = 'radio'
SELECTED_DATE = 'selected_date'
SELECTED_DAYS_KEY = 'selected_dates'
WORKOUTS = 'workouts'



async def get_data_radio(dialog_manager: DialogManager, **kwargs):

    selected_date: str = dialog_manager.dialog_data[SELECTED_DATE]
    time: list[int] = dialog_manager.dialog_data[SELECTED_DAYS_KEY][selected_date]
    data: list[tuple[int]] = [(t, item) for item, t in enumerate(time)]

    workouts: int = dialog_manager.start_data[WORKOUTS]

    return {RADIO: data, WORKOUTS: workouts}


async def get_exist_data(dialog_manager: DialogManager, **kwargs):

    return dialog_manager.dialog_data
