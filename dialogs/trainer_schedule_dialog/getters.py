import logging

from typing import Any

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd.select import ManagedMultiselect


logger = logging.getLogger(__name__)


WORK = 'work'
SELECTED_DATES = 'selected_dates'
RADIO = 'radio'
SEL = 'sel'
SCHEDULES = 'schedules'


def format_schedule(data: dict) -> str:

    items = sorted(map(int, data[WORK].split(', ')))

    return f'{items[0]}-{items[-1]}'


async def selection_getter(dialog_manager: DialogManager, **kwargs):

    selected = dialog_manager.dialog_data.get(SELECTED_DATES, [])

    data_radio = await get_data_radio(dialog_manager)

    return {
        'selected': ', '.join(sorted(selected)),
        'radio': data_radio[RADIO]
    }


async def get_multiselect_data(dialog_manager: DialogManager, **kwargs):

    widget: ManagedMultiselect = dialog_manager.find(SEL)

    items = {item: '🟢' for item in widget.get_checked()}
    
    return {
        'rows': [(i, i, items.get(str(i), '')) for i in range(24)]
    }

    
async def get_data_radio(dialog_manager: DialogManager, **kwargs):

    data = [(format_schedule(data), id) for id, data in dialog_manager.start_data[SCHEDULES].items()]

    return {'radio': data}
