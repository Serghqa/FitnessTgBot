import logging

from aiogram.types import CallbackQuery

from aiogram_dialog import Data, DialogManager, ShowMode
from aiogram_dialog.api.entities.context import Context
from aiogram_dialog.api.internal import RawKeyboard
from aiogram_dialog.widgets.kbd import (
    Button,
    Calendar,
    CalendarScope,
    ManagedCalendar,
    ManagedMultiselect,
    ManagedRadio,
    Multiselect,
    SwitchTo,
)
from aiogram_dialog.widgets.kbd.calendar_kbd import (
    DATE_TEXT,
    TODAY_TEXT,
    CalendarDaysView,
    CalendarMonthView,
    CalendarScopeView,
    CalendarYearsView,
    CalendarUserConfig,
)
from aiogram_dialog.widgets.text import Format, Text

from babel.dates import get_day_names, get_month_names

from datetime import date, datetime

from zoneinfo import ZoneInfo

from typing import Callable, Literal, TypeVar

from db import (
    add_trainer_schedule,
    get_clients_training,
    get_trainer_schedules,
    cancel_trainer_schedule,
    cancel_training_db,
    TrainerSchedule,
    update_working_day,
)
from schemas import SelectedDateSchema, WorkDaySchema
from taskiq_broker import schedule_source
from notification import send_notification
from states import TrainerScheduleStates
from timezones import get_current_date


logger = logging.getLogger(__name__)

T = TypeVar("T")
TypeFactory = Callable[[str], T]

CLIENT_ID = 'id'
DATA = 'data'
DATE = 'date'
RADIO_WORK = 'radio_work'
SCHEDULES = 'schedules'
SEL = 'sel'
SEL_D = 'sel_d'
SELECTED_DATE = 'selected_date'
SELECTED_DATES = 'selected_dates'
TIME = 'time'
TIME_ZONE = 'time_zone'
TRAINER_ID = 'trainer_id'
TRAININGS = 'trainings'


class WeekDay(Text):

    async def _render_text(self, data, dialog_manager: DialogManager) -> str:

        selected_date: date = data[DATE]
        locale = dialog_manager.event.from_user.language_code

        return get_day_names(
            width='short',
            context='stand-alone',
            locale=locale,
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
            radio_item = selected[serial_date]
            if isinstance(radio_item, str):
                return self.mark[int(radio_item)]
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

    async def _get_user_config(
            self,
            data: dict,
            manager: DialogManager,
    ) -> CalendarUserConfig:
        """
        User related config getter.

        Override this method to customize how user config is retrieved.

        :param data: data from window getter
        :param manager: dialog manager instance
        :return:
        """

        tz = ZoneInfo(manager.start_data.get(TIME_ZONE))

        calendar_config = CalendarUserConfig(
            timezone=tz
        )

        return calendar_config


class CustomMultiselect(Multiselect):

    async def _render_keyboard(
        self,
        data: dict,
        manager: DialogManager,
    ) -> RawKeyboard:

        keyboard = []
        row = []

        for pos, item in enumerate(self.items_getter(data)):
            row.append(
                await self._render_button(pos, item, item, data, manager)
            )
            if len(row) == 6:
                keyboard.append(row)
                row = []

        return keyboard


async def _cancel_schedule_task(
    client_id: int,
    date: str,
    time: int
) -> None:

    schedule_task_id = f'{client_id}_{date}_{time}'

    await schedule_source.delete_schedule(schedule_task_id)
    logger.info(
        'Задача об уведомлении id=%s отменена', schedule_task_id
    )


def _update_selected_dates(selected: dict, today: str) -> None:

    for date_, _ in list(selected.items()):
        if date_ <= today:
            selected.pop(date_)


def _get_curent_widget_context(
    dialog_manager: DialogManager,
    key: str,
    default='1'
) -> str | list[str]:

    context: Context = dialog_manager.current_context()
    widget_data = context.widget_data.get(key, default)

    return widget_data


def _get_sortred_items(work: str) -> list[int]:

    return sorted(map(int, work.split(',')))


def _transform_time(time_: str) -> dict[str, str]:

    items: list[int] = sorted(map(int, time_.split(',')))
    start, stop = min(items), max(items)
    breaks: str = ','.join(
        str(item) for item in range(start, stop+1) if item not in items
    ) or 'нет'

    return {'start': str(start), 'stop': str(stop), 'breaks': breaks}


async def on_date_selected(
    callback: CallbackQuery,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date
):

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_date(timezone)

    serial_date = clicked_date.isoformat()

    selected: dict = dialog_manager.dialog_data.get(SELECTED_DATES, {})

    _update_selected_dates(selected, today.date().isoformat())

    if today.date().isoformat() < serial_date:

        if serial_date in selected:

            if isinstance(selected[serial_date], str):

                selected.pop(serial_date)
            else:

                selected_data: dict[str, str] = \
                    SelectedDateSchema(**selected[serial_date]).model_dump()

                trainings: list[dict] = await get_clients_training(
                    dialog_manager=dialog_manager,
                    date_=serial_date,
                )

                dialog_manager.dialog_data[SELECTED_DATE] = {
                    DATE: serial_date,
                    DATA: selected_data,
                    TRAININGS: trainings
                }

                await dialog_manager.switch_to(
                    state=TrainerScheduleStates.selected_date,
                    show_mode=ShowMode.EDIT,
                )

        else:
            widget_item: Literal['1', '2', '3'] = \
                _get_curent_widget_context(
                    dialog_manager=dialog_manager,
                    key=RADIO_WORK,
                )

            selected[serial_date] = widget_item


async def revoke(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    context: Context = dialog_manager.current_context()

    items: list[str] = context.widget_data.get(SEL_D, [])
    items.clear()

    await update_selected_dates(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager,
    )


async def update_selected_dates(
    callback: CallbackQuery,
    widget: SwitchTo | Button,
    dialog_manager: DialogManager
):

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_date(timezone)

    selected: dict = dialog_manager.dialog_data[SELECTED_DATES]
    _update_selected_dates(selected, today.date().isoformat())

    del dialog_manager.dialog_data[SELECTED_DATE]

    await set_radio_calendar(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager,
    )


async def cancel_training(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    context: Context = dialog_manager.current_context()

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_date(timezone)

    if today.date().isoformat() >= \
            dialog_manager.dialog_data[SELECTED_DATE][DATE]:

        await update_selected_dates(
            callback=callback,
            widget=widget,
            dialog_manager=dialog_manager,
        )
        await dialog_manager.switch_to(
            state=TrainerScheduleStates.schedule,
            show_mode=ShowMode.EDIT,
        )
        await callback.answer(
            text='Данные устарели, попробуйте еще раз, пожалуйста.',
            show_alert=True,
        )

    else:

        items: list[str] = context.widget_data.get(SEL_D, [])

        trainings: list[dict] = \
            dialog_manager.dialog_data[SELECTED_DATE][TRAININGS]

        for item in items:
            data_training: dict = trainings[int(item)]
            result = await cancel_training_db(
                dialog_manager=dialog_manager,
                client_id=data_training[CLIENT_ID],
                trainer_id=data_training[TRAINER_ID],
                date_=data_training[DATE],
                time_=data_training[TIME],
            )

            if result:

                text = (
                    f'Ваше занятие в группе {data_training[TRAINER_ID]} '
                    f'{data_training[DATE]} в '
                    f'{data_training[TIME]}:00 отменено.'
                )

                await send_notification(
                    bot=dialog_manager.event.bot,
                    user_id=data_training[CLIENT_ID],
                    text=text,
                )

                await _cancel_schedule_task(
                    client_id=data_training[CLIENT_ID],
                    date=data_training[DATE],
                    time=data_training[TIME],
                )

        trainings: list[dict] = [
            training for i, training in enumerate(trainings)
            if str(i) not in items
        ]

        dialog_manager.dialog_data[SELECTED_DATE][TRAININGS] = trainings

    if SEL_D in context.widget_data:
        context.widget_data[SEL_D].clear()


async def cancel_work(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    context: Context = dialog_manager.current_context()

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_date(timezone)

    work_date: str = dialog_manager.dialog_data[SELECTED_DATE][DATE]

    if today.date().isoformat() >= work_date:
        await callback.answer(
            text='Данные устарели, попробуйте еще раз, пожалуйста.',
            show_alert=True,
        )
        await update_selected_dates(
            callback=callback,
            widget=widget,
            dialog_manager=dialog_manager,
        )

    else:
        trainings: list[dict] = \
            dialog_manager.dialog_data[SELECTED_DATE][TRAININGS]

        for training in trainings:
            result = await cancel_training_db(
                dialog_manager=dialog_manager,
                client_id=training[CLIENT_ID],
                trainer_id=training[TRAINER_ID],
                date_=training[DATE],
                time_=training[TIME],
            )

            if result:
                text = (
                    f'Ваше занятие в группе {training[TRAINER_ID]} '
                    f'{training[DATE]} в {training[TIME]}:00 отменено.'
                )

                await send_notification(
                    bot=dialog_manager.event.bot,
                    user_id=training[CLIENT_ID],
                    text=text,
                )

                await _cancel_schedule_task(
                    client_id=training[CLIENT_ID],
                    date=training[DATE],
                    time=training[TIME],
                )

        await cancel_trainer_schedule(
            dialog_manager=dialog_manager,
            date_=work_date,
        )

        dialog_manager.dialog_data.pop(SELECTED_DATE)
        dialog_manager.dialog_data[SELECTED_DATES].pop(work_date)

    if SEL_D in context.widget_data:
        context.widget_data[SEL_D].clear()


async def apply_selected(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_date(timezone)

    selected_dates: dict = dialog_manager.dialog_data.get(SELECTED_DATES)

    now_selected: dict = {
        date_: item for date_, item in selected_dates.items()
        if isinstance(item, str) and today.date().isoformat() < date_
    }

    if now_selected:
        await add_trainer_schedule(
            dialog_manager=dialog_manager,
            data=now_selected,
        )

        for date_, item in now_selected.items():
            time_: str = dialog_manager.start_data[SCHEDULES][item]
            data: dict = _transform_time(time_)
            dialog_manager.dialog_data[SELECTED_DATES][date_] = data


async def set_radio_work(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    radio: ManagedRadio = dialog_manager.find(RADIO_WORK)
    widget_item: Literal['1', '2', '3'] = _get_curent_widget_context(
        dialog_manager=dialog_manager,
        key=RADIO_WORK
    )

    await radio.set_checked(widget_item)


async def set_radio_calendar(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    radio: ManagedRadio = dialog_manager.find(RADIO_WORK)
    widget_item: Literal['1', '2', '3'] = \
        _get_curent_widget_context(dialog_manager, RADIO_WORK)

    await radio.set_checked(widget_item)

    schedules: list[TrainerSchedule] = \
        await get_trainer_schedules(dialog_manager)
    selected: dict = dialog_manager.dialog_data.setdefault(SELECTED_DATES, {})

    for schedule in schedules:
        selected[schedule.date.isoformat()] =\
            _transform_time(schedule.time)


async def set_checked(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    widget_item: Literal['1', '2', '3'] = _get_curent_widget_context(
        dialog_manager=dialog_manager,
        key=RADIO_WORK,
    )

    await _set_checked(
        dialog_manager=dialog_manager,
        id=widget_item
    )


async def _set_checked(dialog_manager: DialogManager, id: str):

    work: str = dialog_manager.start_data[SCHEDULES][id]
    multiselect: CustomMultiselect = dialog_manager.find(SEL)

    for item in _get_sortred_items(work):
        await multiselect.set_checked(item, True)


async def process_selection(
    callback: CallbackQuery,
    widget: ManagedRadio,
    dialog_manager: DialogManager,
    item_id: str
):

    items: list[int] = \
        _get_sortred_items(dialog_manager.start_data[SCHEDULES][item_id])
    breaks = \
        ','.join(
            [str(i) for i in range(items[0], items[-1]) if i not in items]
        ) or 'нет'

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

    widget_item: Literal['1', '2', '3'] = \
        _get_curent_widget_context(dialog_manager, RADIO_WORK)
    widget_data: list[str] = _get_curent_widget_context(dialog_manager, SEL)
    selected: list[int] = sorted(map(int, widget_data))

    work = ','.join(map(str, selected))

    work_schema: WorkDaySchema = WorkDaySchema(
        item=widget_item,
        work=work,
    )

    await update_working_day(
        dialog_manager=dialog_manager,
        id=work_schema.item,
        value=work_schema.work,
    )
    await reset_checked(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager
    )

    dialog_manager.start_data[SCHEDULES][work_schema.item] = work_schema.work


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

    widget_item: Literal['1', '2', '3'] = _get_curent_widget_context(
        dialog_manager=dialog_manager,
        key=RADIO_WORK,
    )
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
    context.widget_data[RADIO_WORK] = start_data['widget_data'][RADIO_WORK]
