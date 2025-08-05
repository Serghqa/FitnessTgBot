import logging

from aiogram import Bot

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import ManagedRadio, SwitchTo, Calendar, CalendarScope, ManagedCalendar, Radio, Button
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
    CalendarYearsView
)
from aiogram_dialog.widgets.kbd.select import ManagedMultiselect
from aiogram_dialog.api.internal import RawKeyboard

from babel.dates import get_day_names, get_month_names

from db import get_trainer_schedules, get_schedules, get_schedule, Trainer, Client, Schedule, TrainerSchedule, Workout, add_training, get_client_trainings, cancel_training_db, get_workouts

from datetime import date

from states import ClientState


logger = logging.getLogger(__name__)

EXIST = 'exist'
TRAINER_ID = 'trainer_id'
DATE = 'date'
TIME = 'time'
SELECTED_DATES = 'selected_dates'
SELECTED_DATE = 'selected_date'
SEL_D = 'sel_d'
SIGN_UP = 'sign_up'
CAL = 'cal'
WORKOUTS = 'workouts'
RAD_SCHED = 'rad_sched'
MY_SIGN = 'my_sign'


def split_time(value: str, delimiter=',') -> list[int]:

    return list(map(int, value.split(delimiter)))


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
        selected = dialog_manager.dialog_data.get(SELECTED_DATES, {})

        if serial_date in selected:
            item_mark: int = dialog_manager.dialog_data.get(MY_SIGN, 0)
            return self.mark[item_mark]

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
                date_text=MarkedDay("🔴🟢", DATE_TEXT),
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


async def update_workouts(
    callback: CallbackQuery,
    dialog_manager: DialogManager,
    trainer_id: int
) -> None:

    workout: Workout = await get_workouts(
        dialog_manager=dialog_manager,
        trainer_id=trainer_id,
        client_id=dialog_manager.event.from_user.id
    )

    if workout.workouts != dialog_manager.start_data[WORKOUTS]:
        await callback.answer(
            text='Данные были изменены!',
            show_alert=True
        )

    dialog_manager.start_data[WORKOUTS] = workout.workouts


async def set_calendar(
    callback: CallbackQuery,
    widget: SwitchTo | ManagedCalendar,
    dialog_manager: DialogManager
) -> None:

    trainer_schedules: list[TrainerSchedule] = await get_trainer_schedules(
        dialog_manager,
        dialog_manager.start_data[TRAINER_ID]
    )

    schedules: list[Schedule] = await get_schedules(
        dialog_manager,
        dialog_manager.start_data[TRAINER_ID]
    )

    data_schedules: dict[str, list[int]] = {
        schedule.date: split_time(schedule.time)
        for schedule in trainer_schedules
    }

    for schedule in schedules:  # Schedule
        if schedule.date in data_schedules:
            if schedule.time in data_schedules[schedule.date]:
                data_schedules[schedule.date].remove(schedule.time)
                if not data_schedules[schedule.date]:
                    data_schedules.pop(schedule.date)

    dialog_manager.dialog_data[SELECTED_DATES] = data_schedules

    dialog_manager.dialog_data[MY_SIGN] = 0

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

    today: str = date.today().isoformat()

    if clicked_date.isoformat() in dialog_manager.dialog_data[SELECTED_DATES]:

        if today > clicked_date.isoformat():

            await callback.answer(
                text='Данные устарели, попробуйте еще раз, пожалуйста.',
                show_alert=True,
            )
            await set_calendar(
                callback,
                widget,
                dialog_manager
            )

        else:

            await update_workouts(
                callback=callback,
                dialog_manager=dialog_manager,
                trainer_id=dialog_manager.start_data[TRAINER_ID]
            )

            dialog_manager.dialog_data[SELECTED_DATE] = \
                clicked_date.isoformat()

            await dialog_manager.switch_to(
                state=ClientState.sign_training,
                show_mode=ShowMode.EDIT,
            )


async def on_date(
    callback: CallbackQuery,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date, /,
):

    today: str = date.today().isoformat()

    if clicked_date.isoformat() in dialog_manager.dialog_data[SELECTED_DATES]:

        if today >= clicked_date.isoformat():

            callback.answer(
                text='Данные устарели, попробуйте еще раз, пожалуйста.',
                show_alert=True,
            )
            await set_client_trainings(
                callback,
                widget,
                dialog_manager
            )

        else:

            dialog_manager.dialog_data[SELECTED_DATE] = \
                clicked_date.isoformat()

            await dialog_manager.switch_to(
                state=ClientState.cancel_training,
                show_mode=ShowMode.EDIT,
            )


async def clear_data(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
) -> None:

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

    radio: ManagedRadio = dialog_manager.find(RAD_SCHED)

    await radio.set_checked(0)


async def exist_sign(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    context: Context = dialog_manager.current_context()
    today: str = date.today().isoformat()

    radio_item: str = context.widget_data.get(RAD_SCHED)

    client_id: int = dialog_manager.event.from_user.id
    trainer_id: int = dialog_manager.start_data[TRAINER_ID]
    date_: str = dialog_manager.dialog_data[SELECTED_DATE]
    time_: int = dialog_manager.dialog_data[SELECTED_DATES][date_][int(radio_item)]

    schedule: Schedule | None = await get_schedule(
        dialog_manager=dialog_manager,
        date=date_,
        time=time_,
        trainer_id=trainer_id
    )

    dialog_manager.dialog_data[EXIST] = schedule is None and today < date_

    if schedule is None:
        await add_training(
            dialog_manager=dialog_manager,
            date_=date_,
            client_id=client_id,
            trainer_id=trainer_id,
            time_=time_
        )


async def set_client_trainings(
    callback: CallbackQuery,
    widget: SwitchTo | ManagedCalendar | Button,
    dialog_manager: DialogManager
):

    selected_dates: dict = dialog_manager.dialog_data[SELECTED_DATES]
    selected_dates.clear()

    schedules: list[Schedule] = await get_client_trainings(
        dialog_manager=dialog_manager,
        trainer_id=dialog_manager.start_data[TRAINER_ID],
        client_id=dialog_manager.event.from_user.id
    )
    for schedule in schedules:
        selected_dates.setdefault(schedule.date, []).append(schedule.time)

    dialog_manager.dialog_data[MY_SIGN] = 1


async def reset_widget(
    callback: CallbackQuery,
    widget: SwitchTo | Button,
    dialog_manager: DialogManager
):

    multiselect: ManagedMultiselect = dialog_manager.find(SEL_D)
    await multiselect.reset_checked()


async def cancel_training(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    today: str = date.today().isoformat()

    context: Context = dialog_manager.current_context()

    selected_date: str = dialog_manager.dialog_data[SELECTED_DATE]

    if today < selected_date:

        times: list[int] = dialog_manager.dialog_data[SELECTED_DATES][selected_date]
        items = list(map(int, context.widget_data.get(SEL_D)))

        for item in items:
            time_: int = times[item]

            await cancel_training_db(
                dialog_manager,
                dialog_manager.event.from_user.id,
                dialog_manager.start_data[TRAINER_ID],
                selected_date,
                time_
            )

        times = [t for i, t in enumerate(times) if i not in items]
        if times:
            dialog_manager.dialog_data[SELECTED_DATES][selected_date] = times
        else:
            dialog_manager.dialog_data[SELECTED_DATES].pop(selected_date)

        await reset_widget(
            callback,
            widget,
            dialog_manager
        )

    else:

        await callback.answer(
            text='Данные устарели, попробуйте еще раз, пожалуйста.',
            show_alert=True,
        )

        await set_client_trainings(
            callback,
            widget,
            dialog_manager
        )

        await dialog_manager.switch_to(
            state=ClientState.my_sign_up,
            show_mode=ShowMode.EDIT,
        )
