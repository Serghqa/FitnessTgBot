import logging

from typing import Any, Callable, TypeVar

from aiogram.types import CallbackQuery

from aiogram_dialog.api.internal import RawKeyboard
from aiogram_dialog import ChatEvent, DialogManager, ShowMode, Data
from aiogram_dialog.api.entities.context import Context
from aiogram_dialog.widgets.text import Format, Text
from aiogram_dialog.widgets.kbd import (
    Button,
    Calendar,
    SwitchTo,
    CalendarScope,
    Multiselect,
    ManagedCalendar,
    ManagedMultiselect,
    ManagedRadio
)
from aiogram_dialog.widgets.kbd.calendar_kbd import (
    DATE_TEXT,
    TODAY_TEXT,
    CalendarDaysView,
    CalendarMonthView,
    CalendarScopeView,
    CalendarYearsView,
)

from babel.dates import get_day_names, get_month_names

from datetime import date

from random import randint

from db import (
    get_trainings,
    update_working_day,
    add_trainer_schedule,
    get_trainer_schedules,
    add_training,
    cancel_training_db,
    cancel_trainer_schedule
)

from states import TrainerScheduleStates


logger = logging.getLogger(__name__)


T = TypeVar("T")
TypeFactory = Callable[[str], T]

SELECTED_DAYS_KEY = 'selected_dates'
DATE = 'date'
TIME = 'time'
RADIO_WORK = 'radio_work'
RADIO_CAL = 'radio_cal'
SCHEDULES = 'schedules'
WORK = 'work'
SEL = 'sel'
START = 'start'
STOP = 'stop'
BREAKS = 'breaks'
WIDGET_DATA = 'widget_data'
SELECTED_DATE = 'selected_date'
DATA = 'data'
CLIENTS = 'clients'
SEL_D = 'sel_d'
CLIENT_ID = 'client_id'
TRAINER_ID = 'trainer_id'


class WeekDay(Text):

    async def _render_text(self, data, dialog_manager: DialogManager) -> str:

        selected_date: date = data[DATE]
        locale = dialog_manager.event.from_user.language_code

        return get_day_names(
            width='short', context='stand-alone', locale=locale,
        )[selected_date.weekday()].title()


class MarkedDay(Text):

    def __init__(self, mark: str, other: Text):

        super().__init__()
        self.mark = mark
        self.other = other

    async def _render_text(self, data, dialog_manager: DialogManager) -> str:

        current_date: date = data[DATE]
        serial_date = current_date.isoformat()
        selected = dialog_manager.dialog_data.get(SELECTED_DAYS_KEY, {})

        if serial_date in selected:
            radio_item = selected[serial_date]
            if isinstance(radio_item, int):
                return self.mark[radio_item]
            return '🔴'

        return await self.other.render_text(data, dialog_manager)


class Month(Text):

    async def _render_text(self, data, dialog_manager: DialogManager) -> str:

        selected_date: date = data[DATE]
        locale = dialog_manager.event.from_user.language_code

        return get_month_names(
            'wide', context='stand-alone', locale=locale,
        )[selected_date.month].title()


class CustomCalendar(Calendar):

    def _init_views(self) -> dict[CalendarScope, CalendarScopeView]:

        return {
            CalendarScope.DAYS: CalendarDaysView(
                self._item_callback_data,
                date_text=MarkedDay(" 🟢🔵🟣", DATE_TEXT),
                today_text=MarkedDay("⭕", TODAY_TEXT),
                header_text='~~~~~ ' + Month() + ' ~~~~~',
                weekday_text=WeekDay(),
                next_month_text=Month() + ' >>',
                prev_month_text='<< ' + Month(),
            ),
            CalendarScope.MONTHS: CalendarMonthView(
                self._item_callback_data,
                month_text=Month(),
                header_text='~~~~~ ' + Format('{date:%Y}') + ' ~~~~~',
                this_month_text='[' + Month() + ']',
            ),
            CalendarScope.YEARS: CalendarYearsView(
                self._item_callback_data,
            ),
        }


class CustomMultiselect(Multiselect):

    async def _render_keyboard(
        self,
        data: dict,
        manager: DialogManager,
    ) -> RawKeyboard:
        
        keyboard = []
        row = []

        for pos, item in enumerate(self.items_getter(data)):
            row.append(await self._render_button(pos, item, item, data, manager))
            if len(row) == 6:
                keyboard.append(row)
                row = []
        
        return keyboard
    

def _update_selected_dates(selected: dict, today: str) -> None:

    for date_, _ in list(selected.items()):
        if date_ <= today:
            selected.pop(date_)


def _get_curent_widget_context(
    dialog_manager: DialogManager,
    key: str,
    default='1'
) -> Any:

    context: Context = dialog_manager.current_context()
    widget_data = context.widget_data.get(key, default)

    return widget_data


def _get_sortred_items(work: str) -> list[int]:

    return sorted(map(int, work.split(',')))


def _transform_time(data: str) -> dict:

    items: list[int] = sorted(map(int, data.split(',')))
    start, stop = min(items), max(items)
    breaks: str = ','.join(str(item) for item in range(start, stop+1) if item not in items) or 'нет'

    return {START: start, STOP: stop, BREAKS: breaks}


async def on_date_selected(
    callback: CallbackQuery,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date, /,
):

    today = date.today().isoformat()
    serial_date = clicked_date.isoformat()

    selected: dict = dialog_manager.dialog_data.get(SELECTED_DAYS_KEY, {})

    _update_selected_dates(selected, today)
    
    if today < serial_date:
        
        widget_item = _get_curent_widget_context(dialog_manager, RADIO_WORK)

        if serial_date in selected:
            if isinstance(selected[serial_date], int):
                selected.pop(serial_date)
            else:
                data: dict = selected[serial_date]

                clients: list[dict] = await get_trainings(
                    dialog_manager,
                    serial_date
                )

                dialog_manager.dialog_data[SELECTED_DATE] = {
                    DATE: serial_date,
                    DATA: data,
                    CLIENTS: clients
                }

                await dialog_manager.switch_to(
                    state=TrainerScheduleStates.selected_date,
                    show_mode=ShowMode.EDIT
                )

        else:
            selected[serial_date] = int(widget_item)
        

async def clear_selected_date(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):
    today: str = date.today().isoformat()
    selected: dict = dialog_manager.dialog_data[SELECTED_DAYS_KEY]

    del dialog_manager.dialog_data[SELECTED_DATE]
    _update_selected_dates(selected, today)


async def cancel_training(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):
    
    today: str = date.today().isoformat()

    if today >= dialog_manager.dialog_data[SELECTED_DATE][DATE]:
        await callback.answer(
            text='Данные устарели, попробуйте еще раз, пожалуйста.',
            show_alert=True,
        )
        await dialog_manager.switch_to(
            state=TrainerScheduleStates.schedule,
            show_mode=ShowMode.EDIT,
        )

    context: Context = dialog_manager.current_context()

    items: list[str] = context.widget_data.get(SEL_D, [])
     
    clients: list[dict] = dialog_manager.dialog_data[SELECTED_DATE][CLIENTS]

    for item in items:
        client: dict = clients[int(item)]
        await cancel_training_db(
            dialog_manager,
            client[CLIENT_ID],
            client[TRAINER_ID],
            client[DATE],
            client[TIME]
        )

    clients: list[dict] = [client for i, client in enumerate(clients) if str(i) not in items]

    dialog_manager.dialog_data[SELECTED_DATE][CLIENTS] = clients
    if SEL_D in context.widget_data:
        context.widget_data[SEL_D].clear()


async def cancel_work(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):
    
    context: Context = dialog_manager.current_context()

    clients: list[dict] = dialog_manager.dialog_data[SELECTED_DATE][CLIENTS]

    for client in clients:
        await cancel_training_db(
            dialog_manager,
            client[CLIENT_ID],
            client[TRAINER_ID],
            client[DATE],
            client[TIME]
        )

    work_date: str = dialog_manager.dialog_data[SELECTED_DATE][DATE]

    await cancel_trainer_schedule(
        dialog_manager,
        work_date
    )

    dialog_manager.dialog_data.pop(SELECTED_DATE)
    dialog_manager.dialog_data[SELECTED_DAYS_KEY].pop(work_date)
    if SEL_D in context.widget_data:
        context.widget_data.clear()


async def apply_selected(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    selected: dict = {
        date_: item for date_, item in \
            dialog_manager.dialog_data.get(SELECTED_DAYS_KEY).items() \
                if isinstance(item, int)
    }

    today = date.today().isoformat()

    _update_selected_dates(selected, today)

    if selected:
        await add_trainer_schedule(dialog_manager, selected)
        
        for date_, item in selected.items():
            time: str = dialog_manager.start_data[SCHEDULES][item]
            value: dict = _transform_time(time)
            dialog_manager.dialog_data[SELECTED_DAYS_KEY][date_] = value

            ############### Удалить ###############
            #for id in range(100_000_000, 100_000_005):
            #    t = id - 100_000_000 + 10
            #    await add_training(
            #        dialog_manager,
            #        date_,
            #        id,
            #        dialog_manager.event.from_user.id,
            #        t
            #    )


async def set_radio_work(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    radio: ManagedRadio = dialog_manager.find(RADIO_WORK)
    widget_item: str = _get_curent_widget_context(dialog_manager, RADIO_WORK)

    await radio.set_checked(widget_item)


async def set_radio_calendar(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):
    
    radio: ManagedRadio = dialog_manager.find(RADIO_WORK)
    widget_item: str = _get_curent_widget_context(dialog_manager, RADIO_WORK)

    await radio.set_checked(widget_item)

    selected_db: list[dict] = await get_trainer_schedules(dialog_manager)
    selected: dict = dialog_manager.dialog_data.setdefault(SELECTED_DAYS_KEY, {})

    for data in selected_db:
        selected[data[DATE]] = _transform_time(data[TIME])


async def set_checked(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):
    
    widget_item: str = _get_curent_widget_context(dialog_manager, RADIO_WORK)

    await _set_checked(dialog_manager, int(widget_item))


async def _set_checked(dialog_manager: DialogManager, id: int):  
    
    data: dict[str, Any] = dialog_manager.start_data[SCHEDULES][id]
    multiselect: CustomMultiselect = dialog_manager.find(SEL)

    for item in _get_sortred_items(data):
        await multiselect.set_checked(item, True)


async def process_selection(
    callback: CallbackQuery,
    widget: ManagedRadio,
    dialog_manager: DialogManager,
    item_id: str
):
    
    items: list[int] = _get_sortred_items(dialog_manager.start_data[SCHEDULES][int(item_id)])
    breaks = ','.join([str(i) for i in range(items[0], items[-1]) if i not in items]) or 'нет'

    message = f'Работа с {items[0]} до {items[-1]}\n'\
        f'Перерыв: {breaks}'
    
    await callback.answer(message)


async def reset_checked(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager 
):
    
    multiselect: ManagedMultiselect = dialog_manager.find(SEL)

    await multiselect.reset_checked()


async def apply_work(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    widget_item: str = _get_curent_widget_context(dialog_manager, RADIO_WORK)
    widget_data: list[str] = _get_curent_widget_context(dialog_manager, SEL)
    selected: list[int] = sorted(map(int, widget_data))

    work = ','.join(map(str, selected))

    await update_working_day(dialog_manager, int(widget_item), work)
    await reset_checked(callback, widget, dialog_manager)

    dialog_manager.start_data[SCHEDULES][int(widget_item)] = work


async def reset_calendar(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    dialog_manager.dialog_data.clear()


async def process_result(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
):

    widget_data = {}

    widget_item: str = _get_curent_widget_context(dialog_manager, RADIO_WORK)
    if widget_item:
        widget_data[RADIO_WORK] = widget_item

    await dialog_manager.done(
        result=widget_data,
        show_mode=ShowMode.EDIT)
    

async def process_start(
    start_data: Data,
    dialog_manager: DialogManager
):
    
    context: Context = dialog_manager.current_context()
    context.widget_data[RADIO_WORK] = start_data[WIDGET_DATA][RADIO_WORK]
