import logging

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd.select import ManagedMultiselect
from aiogram_dialog.api.entities import Context

from db import Trainer, get_user


logger = logging.getLogger(__name__)


EXIST = 'exist'
RADIO = 'radio'
RAD_SCHED = 'rad_sched'
RADIO_ITEM = 'radio_item'
ROWS = 'rows'
SELECTED_DATE = 'selected_date'
SELECTED_DATES = 'selected_dates'
SELECTED_TIME = 'selected_time'
SEL_D = 'sel_d'
WORKOUTS = 'workouts'



async def get_data_radio(dialog_manager: DialogManager, **kwargs):

    selected_date: str = dialog_manager.dialog_data[SELECTED_DATE]
    time_: list[int] = dialog_manager.dialog_data[SELECTED_DATES][selected_date]
    data: list[tuple[int]] = [(t, item) for item, t in enumerate(time_)]

    workouts: int = dialog_manager.start_data[WORKOUTS]

    return {RADIO: data, WORKOUTS: workouts}


async def get_exist_data(dialog_manager: DialogManager, **kwargs):

    context: Context = dialog_manager.current_context()

    radio_item: int = int(context.widget_data.get(RAD_SCHED, 0))

    selected_date: str = dialog_manager.dialog_data[SELECTED_DATE]
    selected_time: int = dialog_manager.dialog_data[SELECTED_DATES][selected_date][radio_item]

    return {
        SELECTED_DATE: selected_date,
        SELECTED_TIME: selected_time,
        EXIST: dialog_manager.dialog_data[EXIST]
    }


async def get_data_selected(dialog_manager: DialogManager, **kwargs):

    context: Context = dialog_manager.current_context()

    selected_date: str = dialog_manager.dialog_data[SELECTED_DATE]
    times: list[int] = sorted(dialog_manager.dialog_data[SELECTED_DATES].get(selected_date, []))
    rows: list[tuple[int]] = [(i, t) for i, t in enumerate(times)]
    exist: bool = any(context.widget_data.get(SEL_D, []))

    return {
        SELECTED_DATE: selected_date,
        ROWS: rows,
        EXIST: exist
    }
