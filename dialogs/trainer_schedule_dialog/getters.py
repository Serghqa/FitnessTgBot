import logging

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd.select import ManagedMultiselect
from aiogram_dialog.api.entities import Context


logger = logging.getLogger(__name__)


WORK = 'work'
SELECTED_DATES = 'selected_dates'
SELECTED_DATE = 'selected_date'
SELECTED = 'selected'
RADIO = 'radio'
SEL = 'sel'
SCHEDULES = 'schedules'
ROWS = 'rows'
DATE = 'date'
DATA = 'data'
START = 'start'
STOP = 'stop'
BREAKS = 'breaks'
CLIENTS = 'clients'
TIME = 'time'
NAME = 'name'
SEL_D = 'sel_d'
IS_CANCEL = 'is_cancel'
IS_APPLY = 'is_apply'


def format_schedule(data: str) -> str:

    items = sorted(map(int, data.split(',')))

    return f'{items[0]}-{items[-1]}'


async def selection_getter(dialog_manager: DialogManager, **kwargs):

    data_radio: dict[str, list] = await get_data_radio(dialog_manager)

    is_apply: bool = any(
        item for item in dialog_manager.dialog_data[SELECTED_DATES].values() \
            if isinstance(item, int)
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

    marks = {1: '🟢', 2: '🔵', 3: '🟣'}

    data = [
        (format_schedule(data), id, marks[id]) for id, data in \
            dialog_manager.start_data[SCHEDULES].items()
    ]

    return {RADIO: data}


async def get_current_schedule(dialog_manager: DialogManager, **kwargs):

    context: Context = dialog_manager.current_context()

    selected_date: dict = dialog_manager.dialog_data[SELECTED_DATE][DATE]
    clients: list = dialog_manager.dialog_data[SELECTED_DATE][CLIENTS]
    
    rows = [(i, data[NAME], data[TIME]) for i, data in enumerate(clients)]

    is_cancel: bool = any(context.widget_data.get(SEL_D, []))

    return {
        SELECTED_DATE: selected_date,
        ROWS: rows,
        IS_CANCEL: is_cancel
    }
