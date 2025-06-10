import logging

from aiogram import Bot

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import ManagedRadio, SwitchTo, Calendar, CalendarScope, ManagedCalendar, Radio
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
from aiogram_dialog.api.internal import RawKeyboard

from babel.dates import get_day_names, get_month_names

from db import get_trainer_schedules, get_trainings, get_schedule, Trainer, Client, Schedule, add_training, get_data_user

from datetime import date

from states import ClientState


logger = logging.getLogger(__name__)

EXIST = 'exist'
TRAINER_ID = 'trainer_id'
DATE = 'date'
TIME = 'time'
SELECTED_DAYS_KEY = 'selected_dates'
SELECTED_DATE = 'selected_date'
SIGN_UP = 'sign_up'
CAL = 'cal'
WORKOUTS = 'workouts'


def split_time(time: str) -> list[int]:

    return list(map(int, time.split(',')))


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


class CustomRadio(Radio):

    async def _render_keyboard(
        self,
        data: dict,
        manager: DialogManager,
    ) -> RawKeyboard:
        
        keyboard = []
        row = []

        for pos, item in enumerate(self.items_getter(data)):
            row.append(await self._render_button(pos, item, item, data, manager))
            if len(row) == 4:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        
        return keyboard


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

        for schedule in schedules:
            dates[date].remove(schedule[TIME])

        if dates[date]:
            selected_dates[date] = dates[date]

    await reset_radio(
        callback,
        widget,
        dialog_manager
    )


async def on_date_selected(
    callback: CallbackQuery,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date, /,
):

    if clicked_date.isoformat() in dialog_manager.dialog_data[SELECTED_DAYS_KEY]:
        dialog_manager.dialog_data[SELECTED_DATE] = \
            clicked_date.isoformat()
        
        #user_data: Client = await get_data_user(
        #    dialog_manager,
        #    Client,
        #    dialog_manager.start_data[TRAINER_ID]
        #)
        #dialog_manager.start_data[WORKOUTS] = user_data[WORKOUTS]
        
        await dialog_manager.switch_to(
            state=ClientState.sign_training,
            show_mode=ShowMode.EDIT,
        )


async def clear_data(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):
    
    dialog_manager.dialog_data.clear()

    await dialog_manager.switch_to(
        state=ClientState.main,
        show_mode=ShowMode.EDIT,
    )


async def reset_radio(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):
    
    radio: ManagedRadio = dialog_manager.find('rad_sched')

    await radio.set_checked(None)


async def process_selection(
    callback: CallbackQuery,
    widget: ManagedRadio,
    dialog_manager: DialogManager,
    item_id: str
):
    
    selected_date: str = dialog_manager.dialog_data[SELECTED_DATE]
    time: int = dialog_manager.dialog_data[SELECTED_DAYS_KEY][selected_date][int(item_id)]

    dialog_manager.dialog_data[TIME] = time


async def exist_sign(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):
    
    client_id: int = dialog_manager.event.from_user.id
    trainer_id: int = dialog_manager.start_data[TRAINER_ID]
    date: str = dialog_manager.dialog_data[SELECTED_DATE]
    time: int = dialog_manager.dialog_data[TIME]

    # Для теста
    #await add_training(
    #    dialog_manager,
    #    date,
    #    client_id,
    #    trainer_id,
    #    time
    #)

    schedule = await get_schedule(
        dialog_manager,
        date,
        time,
        trainer_id,
        client_id
    )

    dialog_manager.dialog_data[EXIST] = schedule is None

    if schedule is None:
        await add_training(
            dialog_manager,
            date,
            client_id,
            trainer_id,
            time
        )
        dialog_manager.start_data[WORKOUTS] -= 1
