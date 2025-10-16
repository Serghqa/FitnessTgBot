import logging

from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import Context
from aiogram_dialog.widgets.kbd.select import ManagedMultiselect


logger = logging.getLogger(__name__)

CLIENT_NAME = 'name'
DATE = 'date'
IS_APPLY = 'is_apply'
IS_CANCEL = 'is_cancel'
RADIO = 'radio'
ROWS = 'rows'
SEL = 'sel'
SEL_D = 'sel_d'
SELECTED_DATES = 'selected_dates'
SELECTED_DATE = 'selected_date'
SCHEDULES = 'schedules'
TIME = 'time'
TRAININGS = 'trainings'


def format_schedule(work: str) -> str:

    items = sorted(map(int, work.split(',')))

    return f'{items[0]}-{items[-1]}'


async def selection_getter(dialog_manager: DialogManager, **kwargs):

    data_radio: dict[str, list] = await get_data_radio(dialog_manager)

    is_apply: bool = any(
        item for item in dialog_manager.dialog_data[SELECTED_DATES].values()
        if isinstance(item, str)
    )

    return {
        RADIO: data_radio[RADIO],
        IS_APPLY: is_apply
    }


async def get_multiselect_data(dialog_manager: DialogManager, **kwargs):

    widget: ManagedMultiselect = dialog_manager.find(SEL)

    items = {item: '🟢' for item in widget.get_checked()}

    return {
        ROWS: [(i, i, items.get(str(i), '')) for i in range(24)]
    }


async def get_data_radio(dialog_manager: DialogManager, **kwargs):

    marks = {'1': '🟢', '2': '🔵', '3': '🟣'}

    data = [
        (format_schedule(work), id, marks[id]) for id, work in
        dialog_manager.start_data[SCHEDULES].items()
    ]

    return {RADIO: data}


async def get_current_schedule(dialog_manager: DialogManager, **kwargs):

    context: Context = dialog_manager.current_context()

    selected_date: dict = dialog_manager.dialog_data[SELECTED_DATE][DATE]
    trainings: list = dialog_manager.dialog_data[SELECTED_DATE][TRAININGS]

    rows = [
        (i, data[CLIENT_NAME], data[TIME]) for i, data in enumerate(trainings)
    ]

    is_cancel: bool = any(context.widget_data.get(SEL_D, []))

    return {
        SELECTED_DATE: selected_date,
        ROWS: rows,
        IS_CANCEL: is_cancel
    }
