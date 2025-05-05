import logging

from aiogram.types import CallbackQuery

from aiogram_dialog import ChatEvent, DialogManager, ShowMode
from aiogram_dialog.widgets.text import Format, Text
from aiogram_dialog.widgets.kbd import (
    Button,
    Calendar,
    CalendarScope,
    ManagedCalendar,
    ManagedMultiselect
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

from db import DailySchedule, get_daily_schedules
from states import TrainerScheduleStates


logger = logging.getLogger(__name__)


SELECTED_DAYS_KEY = 'selected_dates'


class WeekDay(Text):

    async def _render_text(self, data, manager: DialogManager) -> str:

        selected_date: date = data['date']
        locale = manager.event.from_user.language_code

        return get_day_names(
            width='short', context='stand-alone', locale=locale,
        )[selected_date.weekday()].title()


class MarkedDay(Text):

    def __init__(self, mark: str, other: Text):

        super().__init__()
        self.mark = mark
        self.other = other

    async def _render_text(self, data, manager: DialogManager) -> str:

        current_date: date = data['date']
        serial_date = current_date.isoformat()
        selected = manager.dialog_data.get(SELECTED_DAYS_KEY, [])

        if serial_date in selected:
            return self.mark

        return await self.other.render_text(data, manager)


class Month(Text):

    async def _render_text(self, data, manager: DialogManager) -> str:

        selected_date: date = data['date']
        locale = manager.event.from_user.language_code

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


async def on_date_selected(
    callback: ChatEvent,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date, /,
):

    today = date.today().isoformat()

    selected = dialog_manager.dialog_data.setdefault(SELECTED_DAYS_KEY, [])
    serial_date = clicked_date.isoformat()

    if serial_date in selected:
        selected.remove(serial_date)

    else:
        if today < serial_date:
            selected.append(serial_date)


async def on_work(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    work = {
        'widget_id': widget.widget_id,
        'start': None,
        'stop': None,

    }

    daily_schedules: list[DailySchedule] = \
        await get_daily_schedules(dialog_manager)
    print(daily_schedules)

    dialog_manager.dialog_data.update(work)

    await dialog_manager.switch_to(
        state=TrainerScheduleStates.start_work,
        show_mode=ShowMode.EDIT,
    )


async def on_hour_selected(
    callback: CallbackQuery,
    widget: ManagedMultiselect,
    dialog_manager: DialogManager,
    item_id: str
):

    pass
