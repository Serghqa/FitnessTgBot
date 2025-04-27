from datetime import date
from aiogram import F

from aiogram_dialog import ChatEvent, Dialog, DialogManager, Window
from aiogram_dialog.widgets.text import Format, Const, Text
from aiogram_dialog.widgets.kbd import (
    Button,
    Calendar,
    CalendarScope,
    ManagedCalendar,
    SwitchTo,
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

from states import TrainerScheduleStates
from .handlers import (
    done,
    to_main_schedule_window,
    to_create_schedule,
    on_date_clicked
)


SELECTED_DAYS_KEY = "selected_dates"


class WeekDay(Text):
    async def _render_text(self, data, manager: DialogManager) -> str:
        selected_date: date = data["date"]
        locale = manager.event.from_user.language_code
        return get_day_names(
            width="short", context="stand-alone", locale=locale,
        )[selected_date.weekday()].title()


class MarkedDay(Text):
    def __init__(self, mark: str, other: Text):
        super().__init__()
        self.mark = mark
        self.other = other

    async def _render_text(self, data, manager: DialogManager) -> str:
        current_date: date = data["date"]
        serial_date = current_date.isoformat()
        selected = manager.dialog_data.get(SELECTED_DAYS_KEY, [])
        if serial_date in selected:
            return self.mark
        return await self.other.render_text(data, manager)


class Month(Text):
    async def _render_text(self, data, manager: DialogManager) -> str:
        selected_date: date = data["date"]
        locale = manager.event.from_user.language_code
        return get_month_names(
            "wide", context="stand-alone", locale=locale,
        )[selected_date.month].title()


class CustomCalendar(Calendar):
    def _init_views(self) -> dict[CalendarScope, CalendarScopeView]:
        return {
            CalendarScope.DAYS: CalendarDaysView(
                self._item_callback_data,
                date_text=MarkedDay("🔴", DATE_TEXT),
                today_text=MarkedDay("⭕", TODAY_TEXT),
                header_text="~~~~~ " + Month() + " ~~~~~",
                weekday_text=WeekDay(),
                next_month_text=Month() + " >>",
                prev_month_text="<< " + Month(),
            ),
            CalendarScope.MONTHS: CalendarMonthView(
                self._item_callback_data,
                month_text=Month(),
                header_text="~~~~~ " + Format("{date:%Y}") + " ~~~~~",
                this_month_text="[" + Month() + "]",
            ),
            CalendarScope.YEARS: CalendarYearsView(
                self._item_callback_data,
            ),
        }


async def on_date_selected(
    callback: ChatEvent,
    widget: ManagedCalendar,
    manager: DialogManager,
    clicked_date: date, /,
):
    selected = manager.dialog_data.setdefault(SELECTED_DAYS_KEY, [])
    serial_date = clicked_date.isoformat()
    if serial_date in selected:
        selected.remove(serial_date)
    else:
        selected.append(serial_date)


async def selection_getter(dialog_manager, **_):
    selected = dialog_manager.dialog_data.get(SELECTED_DAYS_KEY, [])
    return {
        "selected": ", ".join(sorted(selected)),
    }


to_back_trainer_dialog = Button(
    text=Const('В тренерскую'),
    id='to_dlg_gr',
    on_click=done,
)


to_main_window = Button(
    text=Const('На главную'),
    id='to_main',
    on_click=to_main_schedule_window,
)


trainer_schedule_dialog = Dialog(
    Window(
        Format(
            text='Главное окно расписания'
        ),
        Button(
            text=Const('Создать расписание'),
            id='to_cre_sched',
            on_click=to_create_schedule,
        ),
        SwitchTo(
            Const('В кастомный календарь'),
            id='to_cast_cal',
            state=TrainerScheduleStates.custom_create_schedule
        ),
        to_back_trainer_dialog,
        state=TrainerScheduleStates.main,
    ),
    Window(
        Const('Default calendar widget'),
        Calendar(
            id='def_cal',
            on_click=on_date_clicked,
        ),
        to_main_window,
        state=TrainerScheduleStates.create_schedule,
    ),
    Window(
        Const('Customized calendar widget'),
        CustomCalendar(
            id='cust_cal',
            on_click=on_date_selected,
        ),
        to_main_window,
        getter=selection_getter,
        state=TrainerScheduleStates.custom_create_schedule,
    ),
)
