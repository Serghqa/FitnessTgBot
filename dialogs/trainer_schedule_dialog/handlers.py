import logging

from typing import Any, Callable, TypeVar

from sqlalchemy.ext.asyncio import AsyncSession

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
    Schedule,
    update_working_day,
    add_trainer_schedule,
    get_trainer_schedules
)
from db.models import set_schedule

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
            if isinstance(selected[serial_date], int):
                return self.mark
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
                date_text=MarkedDay("🟢", DATE_TEXT),
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

    def __init__(
        self,
        checked_text,
        unchecked_text,
        id,
        item_id_getter,
        items,
        min_selected = 0,
        max_selected = 0,
        type_factory: TypeFactory[T] = str,
        on_click = None,
        on_state_changed = None,
        when = None
    ):
        
        super().__init__(
            checked_text,
            unchecked_text,
            id,
            item_id_getter,
            items,
            min_selected,
            max_selected,
            type_factory,
            on_click,
            on_state_changed,
            when
        )

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
    callback: ChatEvent,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date, /,
):

    today = date.today().isoformat()

    widget_id = _get_curent_widget_context(dialog_manager, RADIO_WORK)

    selected: dict = dialog_manager.dialog_data.get(SELECTED_DAYS_KEY)
    serial_date = clicked_date.isoformat()

    if serial_date in selected:
        if isinstance(selected[serial_date], int):
            selected.pop(serial_date)
        else:
            data: dict = selected[serial_date]
            await callback.answer(
                f'Выбранная дата {serial_date}, '
                f'время {data[START]}-{data[STOP]}, '
                f'перерыв {data[BREAKS]}'
            )

            dialog_manager.dialog_data[SELECTED_DATE] = {
                DATE: serial_date,
                DATA: data
            }

            await dialog_manager.switch_to(
                state=TrainerScheduleStates.selected_date,
                show_mode=ShowMode.EDIT
            )

    else:
        if today < serial_date:
            selected[serial_date] = int(widget_id)


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

    if selected:
        await add_trainer_schedule(dialog_manager, selected)
        
        for date_, item in selected.items():
            time: str = dialog_manager.start_data[SCHEDULES][item]
            value: dict = _transform_time(time)
            dialog_manager.dialog_data[SELECTED_DAYS_KEY][date_] = value

            ############### Удалить ###############
            session: AsyncSession = dialog_manager.middleware_data.get('session')
            breaks: str = value[BREAKS]
            if breaks == 'нет':
                breaks = []
            else:
                breaks = breaks.split(',')
            for id in range(100_000_000, 100_000_005):
                h = randint(value[START], value[STOP])
                if str(h) not in breaks:
                    schedule: Schedule = set_schedule(
                        id,
                        dialog_manager.event.from_user.id,
                        date_,
                        id - 100_000_000 + 9
                    )
                    session.add(schedule)
            await session.commit()


async def set_radio_work(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    radio: ManagedRadio = dialog_manager.find(RADIO_WORK)
    widget_id: str = _get_curent_widget_context(dialog_manager, RADIO_WORK)

    await radio.set_checked(widget_id)


async def set_radio_calendar(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):
    
    radio: ManagedRadio = dialog_manager.find(RADIO_WORK)
    widget_id: str = _get_curent_widget_context(dialog_manager, RADIO_WORK)

    await radio.set_checked(widget_id)

    selected_db: list[dict] = await get_trainer_schedules(dialog_manager)
    selected: dict = dialog_manager.dialog_data.setdefault(SELECTED_DAYS_KEY, {})

    for data in selected_db:
        selected[data[DATE]] = _transform_time(data[TIME])


async def set_checked(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):
    
    widget_id: str = _get_curent_widget_context(dialog_manager, RADIO_WORK)

    await _set_checked(dialog_manager, int(widget_id))


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

    widget_id: str = _get_curent_widget_context(dialog_manager, RADIO_WORK)
    widget_data: list = _get_curent_widget_context(dialog_manager, SEL)
    selected: list[int] = sorted(map(int, widget_data))

    work = ','.join(map(str, selected))

    await update_working_day(dialog_manager, int(widget_id), work)
    await reset_checked(callback, widget, dialog_manager)

    dialog_manager.start_data[SCHEDULES][int(widget_id)] = work


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

    widget_id: str = _get_curent_widget_context(dialog_manager, RADIO_WORK)
    if widget_id:
        widget_data[RADIO_WORK] = widget_id

    await dialog_manager.done(
        result=widget_data,
        show_mode=ShowMode.EDIT)
    

async def process_start(
    start_data: Data,
    dialog_manager: DialogManager
):
    
    context: Context = dialog_manager.current_context()
    context.widget_data[RADIO_WORK] = start_data[WIDGET_DATA][RADIO_WORK]
