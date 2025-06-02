import logging

from aiogram import Bot

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode, Data, ChatEvent
from aiogram_dialog.widgets.kbd import Button, Select, ManagedRadio, SwitchTo, Calendar, CalendarScope, ManagedCalendar
from aiogram_dialog.widgets.kbd.select import ManagedRadio
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.text import Text, Format
from aiogram_dialog.api.entities.context import Context
from aiogram_dialog.widgets.kbd.calendar_kbd import (
    DATE_TEXT,
    TODAY_TEXT,
    CalendarDaysView,
    CalendarMonthView,
    CalendarScopeView,
    CalendarYearsView,
)

from babel.dates import get_day_names, get_month_names

from db import get_trainer_schedules, get_trainings, Trainer, Client

from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession


logger = logging.getLogger(__name__)

TRAINER_ID = 'trainer_id'
DATE = 'date'
TIME = 'time'
SELECTED_DAYS_KEY = 'selected_dates'
CAL = 'cal'


def split_time(time: str) -> list[int]:

    return time.split(',')


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



async def send_message(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager,
        text: str
):
    
    bot: Bot = dialog_manager.event.bot
    user_id: int = dialog_manager.start_data[TRAINER_ID]

    await bot.send_message(user_id, text)


async def set_calendar(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    dates: list[dict] = await get_trainer_schedules(
        dialog_manager,
        dialog_manager.start_data[TRAINER_ID]
    )

    dates: dict[str, list[int]] = {
        data[DATE]: split_time(data[TIME]) for data in dates
    }

    selected_dates = dialog_manager.dialog_data[SELECTED_DAYS_KEY] = {}

    for date in dates:
        schedules: list[dict] = await get_trainings(
            dialog_manager,
            date,
            dialog_manager.start_data[TRAINER_ID]
        )

        while schedules:
            schedule: dict = schedules.pop()
            if schedule[TIME] not in dates[date]:
                selected_dates.setdefault(date, []).append(schedule[TIME])
    print(selected_dates)

    #selected_dates = {date: time for date, time in selected_dates.items() if time}


async def on_date_selected(
    callback: ChatEvent,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date, /,
):

    pass