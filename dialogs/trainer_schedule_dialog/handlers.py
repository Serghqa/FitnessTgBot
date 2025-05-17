import logging

from typing import Any, Callable, TypeVar

from aiogram.types import CallbackQuery

from aiogram_dialog.api.internal import RawKeyboard
from aiogram_dialog import ChatEvent, DialogManager, ShowMode
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

from db import update_working_day, add_trainer_schedule, get_trainer_schedules

from states import TrainerScheduleStates


logger = logging.getLogger(__name__)


T = TypeVar("T")
TypeFactory = Callable[[str], T]

SELECTED_DAYS_KEY = 'selected_dates'
DATE = 'date'
RADIO = 'rad'
WORK_DEFAULT = 'work_default'
SCHEDULES = 'schedules'
WORK = 'work'
SEL = 'sel'


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
        selected = dialog_manager.dialog_data.get(SELECTED_DAYS_KEY, [])

        if serial_date in selected:
            return self.mark

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
                date_text=MarkedDay("🔴", DATE_TEXT),
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


async def on_date_selected(
    callback: ChatEvent,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date, /,
):

    today = date.today().isoformat()

    radio: ManagedRadio = dialog_manager.find(RADIO)
    item_id = radio.get_checked()

    selected: dict = dialog_manager.dialog_data.get(SELECTED_DAYS_KEY)
    serial_date = clicked_date.isoformat()

    if serial_date in selected:
        if selected[serial_date] is not None:
            selected.pop(serial_date)
        else:
            print('Выбранная дата была ранее добавленна')

    else:
        if today < serial_date:
            selected[serial_date] = item_id


async def apply_selected(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    selected: dict = dialog_manager.dialog_data.get(SELECTED_DAYS_KEY)

    if any(selected.values()):
        await add_trainer_schedule(dialog_manager, selected)


async def set_radio_default(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    radio: ManagedRadio = dialog_manager.find(RADIO)

    default = dialog_manager.start_data[WORK_DEFAULT]
    await radio.set_checked(default)

    work_days: list[dict] = await get_trainer_schedules(dialog_manager)
    selected = dialog_manager.dialog_data.setdefault(SELECTED_DAYS_KEY, {})

    for data in work_days:
        selected[data[DATE]] = None


def _get_sotred_items(work: str) -> list[int]:

    return sorted(map(int, work.split(', ')))


async def set_checked(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):
    
    work_id = dialog_manager.start_data[WORK_DEFAULT]

    await _set_checked(dialog_manager, int(work_id))


async def _set_checked(dialog_manager: DialogManager, work_id: int):  
    
    data: dict[str, Any] = dialog_manager.start_data[SCHEDULES][work_id]
    multiselect: CustomMultiselect = dialog_manager.find(SEL)

    for item in _get_sotred_items(data[WORK]):
        await multiselect.set_checked(item, True)


async def process_selection(
    callback: CallbackQuery,
    widget: ManagedRadio,
    dialog_manager: DialogManager,
    item_id: str
):
    
    dialog_manager.start_data[WORK_DEFAULT] = item_id
    items: list[int] = _get_sotred_items(dialog_manager.start_data[SCHEDULES][int(item_id)][WORK])
    breaks = ', '.join([str(i) for i in range(items[0], items[-1]) if i not in items]) or 'нет'

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
    widget: Button,
    dialog_manager: DialogManager
):

    id = dialog_manager.start_data[WORK_DEFAULT]
    multiselect: ManagedMultiselect = dialog_manager.find(SEL)

    data: dict[str, Any] = dialog_manager.start_data[SCHEDULES][int(id)]
    items: list[int] = sorted(map(int, multiselect.get_checked()))

    data[WORK] = ', '.join(map(str, items))

    await update_working_day(dialog_manager, int(id), data[WORK])

    await dialog_manager.switch_to(state=TrainerScheduleStates.work)


async def reset_calendar(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):
    
    new_selected = {}
    selected: dict = dialog_manager.dialog_data.get(SELECTED_DAYS_KEY)

    for date, item_id in selected.items():
        if item_id is None:
            new_selected[date] = item_id

    dialog_manager.dialog_data[SELECTED_DAYS_KEY] = new_selected
