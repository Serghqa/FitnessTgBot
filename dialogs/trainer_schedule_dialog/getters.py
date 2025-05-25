import logging

from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd.select import ManagedMultiselect

from sqlalchemy.ext.asyncio import AsyncSession

from db import Trainer, get_user


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


def format_schedule(data: str) -> str:

    items = sorted(map(int, data.split(',')))

    return f'{items[0]}-{items[-1]}'


async def selection_getter(dialog_manager: DialogManager, **kwargs):

    data_radio = await get_data_radio(dialog_manager)

    return {RADIO: data_radio[RADIO]}


async def get_multiselect_data(dialog_manager: DialogManager, **kwargs):

    widget: ManagedMultiselect = dialog_manager.find(SEL)

    items = {item: '🟢' for item in widget.get_checked()}
    
    return {
        ROWS: [(i, i, items.get(str(i), '')) for i in range(24)]
    }

    
async def get_data_radio(dialog_manager: DialogManager, **kwargs):

    data = [
        (format_schedule(data), id) for id, data in \
            dialog_manager.start_data[SCHEDULES].items()
    ]

    return {RADIO: data}


async def get_current_schedule(dialog_manager: DialogManager, **kwargs):

    selected_date: dict = dialog_manager.dialog_data[SELECTED_DATE]
    start, stop = selected_date[DATA][START], selected_date[DATA][STOP]
    breaks = []
    if selected_date[DATA][BREAKS] != 'нет':
        breaks = selected_date[DATA][BREAKS].split(',')
    rows = [(item, item) for item in range(start, stop+1) if str(item) not in breaks]


    session: AsyncSession = dialog_manager.middleware_data.get('session')
    id: int = dialog_manager.event.from_user.id
    user: Trainer = await get_user(session, id, Trainer)
    for client in user.trainings:
        print(client.date, client.time)

    return {
        DATE: selected_date[DATE],
        ROWS: rows
    }
