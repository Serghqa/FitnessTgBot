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
from sqlalchemy.exc import SQLAlchemyError
from typing import Callable, Literal, TypeVar
from zoneinfo import ZoneInfo

from db import (
    add_trainer_schedule,
    get_clients_training,
    get_trainer_schedules,
    cancel_training_db,
    Client,
    Schedule,
    TrainerSchedule,
    update_working_day,
    WorkingDay,
)
from schemas import SelectedDateSchema, WorkDaySchema
from taskiq_broker import schedule_source
from notification import send_notification
from states import TrainerScheduleStates
from timezones import get_current_datetime


logger = logging.getLogger(__name__)

T = TypeVar("T")
TypeFactory = Callable[[str], T]

CLIENT_ID = 'client_id'
CLIENT_NAME = 'client_name'
DATA = 'data'
DATE = 'date'
IS_WORK = 'is_work'
RADIO_WORK = 'radio_work'
SCHEDULE = 'schedule'
SCHEDULES = 'schedules'
SEL = 'sel'
SEL_D = 'sel_d'
SELECTED_DATE = 'selected_date'
SELECTED_DATES = 'selected_dates'
TIME = 'time'
TIME_ZONE = 'time_zone'
TRAINER_ID = 'trainer_id'
TRAININGS = 'trainings'
WIDGET_DATA = 'widget_data'
WORKOUT = 'workout'
WORKOUTS = 'workouts'


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
            if self.mark == '⭕':
                return self.mark
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
    """
    Отменяет задачу уведомления, связанную с записью на тренировку.
    """

    schedule_task_id = f'{client_id}_{date}_{time}'

    await schedule_source.delete_schedule(schedule_task_id)
    logger.info(
        'Задача об уведомлении id=%s отменена', schedule_task_id
    )


async def _set_radio_calendar(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> bool:
    """
    Настраивает радио-виджет и обновляет данные расписания тренера в календаре.
    """

    radio: ManagedRadio = dialog_manager.find(RADIO_WORK)
    widget_item: Literal['1', '2', '3'] = \
        _get_current_widget_context(dialog_manager, RADIO_WORK)

    await radio.set_checked(widget_item)

    try:
        schedules: list[TrainerSchedule] = \
            await get_trainer_schedules(dialog_manager)
    except SQLAlchemyError as error:
        logger.error(
            'Произошла ошибка при попытке получить расписание '
            'тренера trainer_id=%s, path=%s',
            dialog_manager.event.from_user.id, __name__,
            exc_info=error,
        )

        return False

    selected: dict = dialog_manager.dialog_data.setdefault(SELECTED_DATES, {})

    for schedule in schedules:
        selected[schedule.date.isoformat()] =\
            _transform_time(schedule.time)

    return True


def _update_selected_dates(selected: dict, today: str) -> None:
    """
    Обновляет словарь выбранных дат, удаляя из него все записи,
    ключи которых (даты) меньше или равны указанной дате 'today'.
    """

    for date_, _ in list(selected.items()):
        if date_ < today:
            selected.pop(date_)


def _get_current_widget_context(
    dialog_manager: DialogManager,
    key: str,
    default: Literal['1', '2', '3'] = '1'
) -> Literal['1', '2', '3']:
    """
    Извлекает данные, связанные с определённым ключом, из текущего
    контекста виджета.
    """

    context: Context = dialog_manager.current_context()
    widget_item: str = context.widget_data.get(key, default)

    if widget_item in ('1', '2', '3'):
        return widget_item

    else:
        logger.warning(
            'Функция _get_current_widget_context вернула неожиданный '
            'результат widget_item=%s. В связи с чем установлено '
            'дефолтное значение=%s',
            widget_item, default,
        )

        return default


def _get_sorted_items(work: str) -> list[int]:
    """
    Преобразует строку с числами, разделёнными запятыми,
    в отсортированный список целых чисел.
    """

    return sorted(map(int, work.split(',')))


def _transform_time(work_hours_str: str) -> dict[str, str]:
    """
    Преобразует строку с указанием часов работы в словарь с началом, концом
    рабочего дня и перечнем часов перерыва.
    """

    items: list[int] = sorted(map(int, work_hours_str.split(',')))
    start, stop = items[0], items[-1]
    break_list = [
        str(item) for item in range(start, stop+1) if item not in items
    ]
    breaks = ','.join(break_list) or 'нет'

    return {'start': str(start), 'stop': str(stop), 'breaks': breaks}


def _get_data_trainings(
    trainings: list[tuple[Client, Schedule]]
) -> list[dict]:
    """
    Подготавливает данные для отображения в окне
    диалога.
    """

    data_trainings = []

    for client, schedule in trainings:
        schedule_data = {}
        schedule_data[CLIENT_ID] = client.id
        schedule_data[CLIENT_NAME] = client.name
        schedule_data[TIME] = schedule.time
        data_trainings.append(schedule_data)

    return data_trainings


async def on_date_selected(
    callback: CallbackQuery,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date
) -> None:
    """
    Функция обновляет список выбранных дат (удаляя прошедшие), и в зависимости
    от состояния выбранной даты и наличия в ней информации о тренировках,
    либо переключает диалог на экран подробностей
    по выбранной дню, либо добавляет дату в список будущих выбранных дат
    с привязкой к текущему значению виджета работы (work_item).
    """

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_datetime(timezone)

    serial_date = clicked_date.isoformat()

    selected: dict = dialog_manager.dialog_data.get(SELECTED_DATES, {})

    _update_selected_dates(selected, today.date().isoformat())

    if today.date() <= clicked_date:

        if serial_date in selected:

            if isinstance(selected[serial_date], str):

                selected.pop(serial_date)
            else:

                selected_date_data: dict[str, str] = \
                    SelectedDateSchema.model_validate(
                        selected[serial_date]
                    ).model_dump()

                try:
                    trainings: list[tuple[Client, Schedule]] = \
                        await get_clients_training(
                            dialog_manager=dialog_manager,
                            date_=serial_date,
                        )
                except SQLAlchemyError as error:
                    logger.error(
                        'Ошибка при попытке получить список '
                        '(Client, Schedule) для тренера с '
                        'trainer_id=%s, date=%s, path=%s',
                        dialog_manager.event.from_user.id,
                        serial_date, __name__,
                        exc_info=error,
                    )
                    await callback.answer(
                        text='Неудалось получить данные. Обратитесь '
                             'в поддержку.',
                        show_alert=True,
                    )
                    return

                data_trainings = []

                if trainings:
                    data_trainings = _get_data_trainings(trainings)

                dialog_manager.dialog_data[SELECTED_DATE] = {
                    DATE: serial_date,
                    DATA: selected_date_data,
                    TRAININGS: data_trainings
                }

                if today.date() == clicked_date:
                    await dialog_manager.switch_to(
                        state=TrainerScheduleStates.trainer_today,
                        show_mode=ShowMode.EDIT,
                    )
                else:
                    await dialog_manager.switch_to(
                        state=TrainerScheduleStates.selected_date,
                        show_mode=ShowMode.EDIT,
                    )

        else:
            widget_item: Literal['1', '2', '3'] = \
                _get_current_widget_context(
                    dialog_manager=dialog_manager,
                    key=RADIO_WORK,
                )

            selected[serial_date] = widget_item


async def revoke(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Очищает виджет выбора и обновляет список выбранных дат.
    Возвращает к календарю.
    """

    context: Context = dialog_manager.current_context()

    items: list[str] = context.widget_data.get(SEL_D, [])
    items.clear()

    await update_selected_dates(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager,
    )

    result: bool = await _set_radio_calendar(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager,
    )

    if result:
        del dialog_manager.dialog_data[SELECTED_DATE]

        await dialog_manager.switch_to(
            state=TrainerScheduleStates.schedule,
            show_mode=ShowMode.EDIT,
        )
    else:
        await callback.answer(
            text='Не удалось получить ваше расписание, попробуйте еще раз',
            show_alert=True,
        )


async def update_selected_dates(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Обновляет список выбранных дат, удаляя прошедшие.
    """

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_datetime(timezone)

    selected: dict = dialog_manager.dialog_data[SELECTED_DATES]
    _update_selected_dates(selected, today.date().isoformat())


async def cancel_training(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> list[dict] | None:
    """
    Отменяет записи на тренеровку. Если данные устарели
    произойдет переход в окно календаря.
    """

    context: Context = dialog_manager.current_context()

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_datetime(timezone)

    if today.date().isoformat() >= \
            dialog_manager.dialog_data[SELECTED_DATE][DATE]:

        await update_selected_dates(
            callback=callback,
            widget=widget,
            dialog_manager=dialog_manager,
        )
        await callback.answer(
            text='Данные устарели, попробуйте еще раз, пожалуйста.',
            show_alert=True,
        )
        result: bool = await _set_radio_calendar(
            callback=callback,
            widget=widget,
            dialog_manager=dialog_manager,
        )

        if result:
            await dialog_manager.switch_to(
                state=TrainerScheduleStates.schedule,
                show_mode=ShowMode.EDIT,
            )

        return

    else:
        items: list[str] = context.widget_data.get(SEL_D, [])
        trainer_id: int = dialog_manager.event.from_user.id
        selected_date: str = dialog_manager.dialog_data[SELECTED_DATE][DATE]

        trainings: list[dict] = \
            dialog_manager.dialog_data[SELECTED_DATE][TRAININGS]
        try:
            trainings_db: list[tuple[Client, Schedule]] = \
                await get_clients_training(
                    dialog_manager=dialog_manager,
                    date_=selected_date,
                )
        except SQLAlchemyError as error:
            logger.error(
                'Ошибка при попытке получить тренировки клиентов '
                'trainer_id=%s, date=%s, path=%s',
                trainer_id, selected_date, __name__,
                exc_info=error,
            )
            await callback.answer(
                text='Произошла ошибка, попробуйте еще раз.',
                show_alert=True,
            )
            return

        new_trainings: list[dict] = _get_data_trainings(trainings_db)
        if trainings != new_trainings:
            await callback.answer(
                text='Данные были обновлены, попробуйте еще раз.',
                show_alert=True,
            )
            dialog_manager.dialog_data[SELECTED_DATE][TRAININGS] = \
                new_trainings

            return

        cancel_trainings: list[dict] = [trainings[int(item)] for item in items]

        try:
            canceled_trainings_db = await cancel_training_db(
                dialog_manager=dialog_manager,
                selected_date=selected_date,
                trainer_id=trainer_id,
                trainings=cancel_trainings,
            )
        except SQLAlchemyError as error:
            logger.error(
                'Ошибка при попытке отмены расписания '
                'trainer_id=%s, date=%s, path=%s',
                trainer_id, selected_date, __name__,
                exc_info=error,
            )
            await callback.answer(
                text='Не удалось отменить запись, обратитесь '
                     'в службу поддержки.',
                show_alert=True,
            )

            return

        if canceled_trainings_db is not None:
            for row in canceled_trainings_db:
                schedule: Schedule = row[SCHEDULE]
                text = (
                    f'Ваше занятие в группе {trainer_id} '
                    f'{selected_date} в '
                    f'{schedule.time}:00 отменено.'
                )
                await send_notification(
                    bot=dialog_manager.event.bot,
                    user_id=schedule.client_id,
                    text=text,
                )
                await _cancel_schedule_task(
                    client_id=schedule.client_id,
                    date=selected_date,
                    time=schedule.time,
                )
        else:
            logger.error(
                'неудалось загрузить объекты для корректного '
                'удаления расписания '
                'trainer_id=%s, date=%s, path=%s',
                trainer_id, selected_date, __name__,
            )
            await callback.answer(
                text='Не получилось отменить тренировки, '
                     'попробуйте еще раз.',
                show_alert=True,
            )

            return

        trainings: list[dict] = [
            training for i, training in enumerate(trainings)
            if str(i) not in items
        ]

        dialog_manager.dialog_data[SELECTED_DATE][TRAININGS] = trainings

    if SEL_D in context.widget_data:
        context.widget_data[SEL_D].clear()

    return canceled_trainings_db


async def cancel_work(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Отмена рабочего дня тренера.
    """

    schedule_date: str = dialog_manager.dialog_data[SELECTED_DATE][DATE]
    dialog_manager.dialog_data[IS_WORK] = True

    managed: ManagedMultiselect = dialog_manager.find(SEL_D)

    trainings: list[dict] = \
        dialog_manager.dialog_data[SELECTED_DATE][TRAININGS]

    for item, _ in enumerate(trainings):
        await managed.set_checked(item, True)

    canceled_trainings: list[dict] | None = await cancel_training(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager,
    )

    if canceled_trainings is not None:

        result_calendar: bool = await _set_radio_calendar(
            callback=callback,
            widget=widget,
            dialog_manager=dialog_manager,
        )
        if result_calendar:
            dialog_manager.dialog_data.pop(SELECTED_DATE)
            dialog_manager.dialog_data[SELECTED_DATES].pop(schedule_date)

            await dialog_manager.switch_to(
                state=TrainerScheduleStates.schedule,
                show_mode=ShowMode.EDIT,
            )
        else:
            await callback.answer(
                text='Произошла неожиданная ошибка при попытке вернуться '
                     'к окну календаря, попробуйте перезапустить бота.',
                show_alert=True,
            )


async def apply_selected(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Подтверждение выбранных дат для расписания тренера и добавление
    их в базу данных для хранения.
    """

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_datetime(timezone)

    selected_dates: dict = dialog_manager.dialog_data.get(SELECTED_DATES)

    trainer_schedules: dict = {
        date_selected: data for date_selected, data in selected_dates.items()
        if isinstance(data, str) and today.date().isoformat() < date_selected
    }  # {'2025-12-12': '1', '2025-12-13': '2', ...}
    work_schedules: dict[str, str] = \
        dialog_manager.start_data[SCHEDULES]  # {'1': '11,12,..', '2': '11,..}

    if trainer_schedules:
        try:
            await add_trainer_schedule(
                dialog_manager=dialog_manager,
                trainer_schedules=trainer_schedules,
                work_schedules=work_schedules,
            )
        except SQLAlchemyError as error:
            logger.error(
                'Ошибка при попытке добавить расписание '
                'тренера trainer_id=%s, path=%s',
                dialog_manager.event.from_user.id, __name__,
                exc_info=error,
            )
            await callback.answer(
                text='Неудалось сохранить ваше расписание, '
                     'попробуйте еще раз.',
                show_alert=True,
            )
            return

        for date_selected, work_item in trainer_schedules.items():
            str_time: str = dialog_manager.start_data[SCHEDULES][work_item]
            data: dict = _transform_time(str_time)
            dialog_manager.dialog_data[SELECTED_DATES][date_selected] = data

    _update_selected_dates(
        selected=selected_dates,
        today=today.date().isoformat(),
    )


async def set_radio_work(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
) -> None:
    """
    Устанавливает выбранное значение в радио-кнопке, связанной с рабочими
    днями, на основе данных из контекста виджета.
    """

    radio: ManagedRadio = dialog_manager.find(RADIO_WORK)
    widget_item: Literal['1', '2', '3'] = _get_current_widget_context(
        dialog_manager=dialog_manager,
        key=RADIO_WORK,
    )

    await radio.set_checked(widget_item)


async def to_calendar(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:

    """
    Перевод пользователя в окно календаря.
    """

    result: bool = await _set_radio_calendar(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager,
    )

    if result:
        await dialog_manager.switch_to(
            state=TrainerScheduleStates.schedule,
            show_mode=ShowMode.EDIT,
        )
    else:
        await callback.answer(
            text='Не удалось получить ваше расписание, попробуйте еще раз',
            show_alert=True,
        )


async def set_checked_radio(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):
    """
    Устанавливает выбранное значение в радио-кнопке
    на основе данных из контекста виджета.
    """

    widget_item: Literal['1', '2', '3'] = _get_current_widget_context(
        dialog_manager=dialog_manager,
        key=RADIO_WORK,
    )

    await _set_checked(
        dialog_manager=dialog_manager,
        id=widget_item
    )


async def _set_checked(dialog_manager: DialogManager, id: str) -> None:
    """
    Устанавливает выбранные элементы в мультиселекте на
    основе расписания.
    """

    schedules: dict[Literal['1', '2', '3'], str] \
        = dialog_manager.start_data[SCHEDULES]
    schedule: str = schedules[id]  # '10,11,12,13,14'
    multiselect: CustomMultiselect = dialog_manager.find(SEL)

    for item in _get_sorted_items(schedule):
        await multiselect.set_checked(item, True)


async def process_selection(
    callback: CallbackQuery,
    widget: ManagedRadio,
    dialog_manager: DialogManager,
    item_id: str
) -> None:
    """
    Обрабатывает элемент рабочего времени (строка),
    вычисляет перерывы и выводит сообщение с
    информацией о рабочем времени и перерывах.
    """

    # schedules = {1: '10,11,12', 2: '11,12,13,14', 3: '9,10,11'}
    str_times: dict[int, str] = dialog_manager.start_data[SCHEDULES]

    work_times: list[int] = _get_sorted_items(str_times[item_id])
    start_time = work_times[0]
    end_time = work_times[-1]

    all_times = set(range(start_time, end_time))
    breaks_set = all_times - set(work_times)
    break_list = sorted(breaks_set)
    breaks = ','.join(map(str, break_list)) if break_list else 'нет'

    message = f'Рабочее время: {start_time}  {end_time-1}\n'\
        f'Перерыв: {breaks}'

    await callback.answer(message)


async def reset_checked_multiselect(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
) -> None:
    """
    Функция сбрасывает список "выбранных" элементов в виджете,
    идентифицируемом через константу SEL, находящемся внутри текущего окна
    диалога, управляемого dialog_manager.
    """

    multiselect: ManagedMultiselect = dialog_manager.find(SEL)

    await multiselect.reset_checked()


async def apply_work(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
) -> None:
    """
    Применяет изменения в рабочей смене тренера: обновляет расписание
    для выбранной смены и сбрасывает выбранные элементы в мультиселекте.
    """

    widget_item: Literal['1', '2', '3'] = \
        _get_current_widget_context(dialog_manager, RADIO_WORK)

    context: Context = dialog_manager.current_context()
    times_list_raw: list[str] = context.widget_data.get(SEL, [])

    times_list: list[int] = sorted(map(int, times_list_raw))

    work = ','.join(map(str, times_list))

    work_schema: WorkDaySchema = WorkDaySchema(
        item=widget_item,
        work=work,
    )

    try:
        work_day: WorkingDay | None = await update_working_day(
            dialog_manager=dialog_manager,
            item=work_schema.item,
            value=work_schema.work,
        )
    except SQLAlchemyError as error:
        logger.error(
            'Произошла ошибка при попытке обновить WorkingDay тренера '
            'trainer_id=%s, path=%s',
            dialog_manager.event.from_user.id, __name__,
            exc_info=error,
        )
        await callback.answer(
            text='Произошла ошибка при обновлении вашей смены, '
                 'обратитесь в службу поддержки.',
            show_alert=True,
        )
        await reset_checked_multiselect(
            callback=callback,
            widget=widget,
            dialog_manager=dialog_manager
        )
        return

    if work_day is not None:
        dialog_manager.start_data[SCHEDULES][work_schema.item] = \
            work_schema.work

    else:
        logger.error(
            'Неудалось сохранить изменения WorkingDay для '
            ' тренера trainer_id=%s, path=%s.',
            dialog_manager.event.from_user.id, __name__,
        )
        await callback.answer(
            text='Не удалось применить ваши изменения, попробуйте '
                 'еще раз или обратитесь в поддержку.',
            show_alert=True,
        )
    await reset_checked_multiselect(
            callback=callback,
            widget=widget,
            dialog_manager=dialog_manager
        )


async def reset_calendar(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
) -> None:
    """
    Очищает данные, которые могут содержать
    выбранные пользователем даты.
    """

    dialog_manager.dialog_data.clear()


async def process_result(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
) -> None:
    """
    Обрабатывает результат, извлекая текущее значение радио-кнопки,
    и завершает текущий диалог, передавая данные в родительский диалог.
    """

    widget_data = {}

    widget_item: Literal['1', '2', '3'] = _get_current_widget_context(
        dialog_manager=dialog_manager,
        key=RADIO_WORK,
    )
    if widget_item:
        widget_data[RADIO_WORK] = widget_item

    await dialog_manager.done(
        result=widget_data,
        show_mode=ShowMode.EDIT
    )


async def process_start(
    start_data: Data,
    dialog_manager: DialogManager
) -> None:
    """
    Инициализирует контекст виджета, устанавливая начальное значение
    для радио-кнопки, связанной с рабочими днями.
    """

    context: Context = dialog_manager.current_context()
    context.widget_data[RADIO_WORK] = start_data[WIDGET_DATA][RADIO_WORK]
