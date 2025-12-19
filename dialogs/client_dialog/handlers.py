import asyncio
import logging

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.api.entities.context import Context
from aiogram_dialog.api.internal import RawKeyboard
from aiogram_dialog.widgets.kbd import (
    Button,
    Calendar,
    CalendarScope,
    ManagedCalendar,
    ManagedMultiselect,
    ManagedRadio,
    Radio,
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
from datetime import date, datetime, time, timedelta
from sqlalchemy.exc import SQLAlchemyError
from taskiq.scheduler.scheduled_task import ScheduledTask
from zoneinfo import ZoneInfo

from db import (
    add_training,
    cancel_training_db,
    get_client_trainings,
    get_schedules,
    get_schedule_exsists,
    get_trainer_schedule,
    get_trainer_schedules,
    get_workouts,
    Schedule,
    TrainerSchedule,
    Workout,
)
from notification import send_notification
from schemas import ScheduleSchema
from states import ClientState
from tasks import send_scheduled_notification
from taskiq_broker import schedule_source
from timezones import get_current_datetime


logger = logging.getLogger(__name__)

DATE = 'date'
EXIST = 'exist'
MY_SIGN = 'my_sign'
RAD_SCHED = 'rad_sched'
SEL_D = 'sel_d'
SELECTED_DATE = 'selected_date'
SELECTED_DATES = 'selected_dates'
TIME_ZONE = 'time_zone'
TRAINER_ID = 'trainer_id'
WORKOUTS = 'workouts'


def _split_time(value: str, delimiter=',') -> list[int]:

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
                today_text=MarkedDay("⭕⭕", TODAY_TEXT),
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


class CustomRadio(Radio):

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
            if len(row) == 4:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)

        return keyboard


async def update_workouts(
    callback: CallbackQuery,
    dialog_manager: DialogManager,
    trainer_id: int
) -> Workout | None:
    """
    Обновляет количество тренировок клиента.
    """

    client_id: int = dialog_manager.event.from_user.id
    trainer_id: int = dialog_manager.start_data[TRAINER_ID]
    try:
        workout: Workout | None = await get_workouts(
            dialog_manager=dialog_manager,
            trainer_id=trainer_id,
            client_id=dialog_manager.event.from_user.id,
        )
    except SQLAlchemyError as error:
        logger.error(
            'Ошибка при обновлении количества тренировок '
            'клиента client_id=%s, trainer_id=%s, path=%s',
            client_id, trainer_id, __name__,
            exc_info=error,
        )
        return

    if workout is None:
        logger.error(
            'Неудалось получить объект тренировок Workout '
            'клиента client_id=%s, trainer_id=%s, path=%s',
            client_id, trainer_id, __name__,
        )
        return

    if workout.workouts != dialog_manager.start_data[WORKOUTS]:
        await callback.answer(
            text='Количество тренировок было изменено!',
            show_alert=True,
        )

    dialog_manager.start_data[WORKOUTS] = workout.workouts

    return workout


async def _update_calendar(
    dialog_manager: DialogManager,
) -> dict[str, list[int]] | None:
    """
    Получает расписание тренера и фильтрует
    по свободному времени.
    """

    trainer_schedules: list[TrainerSchedule]
    schedules: list[Schedule]

    try:
        trainer_schedules, schedules = await asyncio.gather(
            get_trainer_schedules(
                dialog_manager=dialog_manager,
                trainer_id=dialog_manager.start_data[TRAINER_ID],
            ),
            get_schedules(
                dialog_manager=dialog_manager,
                trainer_id=dialog_manager.start_data[TRAINER_ID],
            )
        )
    except SQLAlchemyError as error:
        logger.error(
            'Ошибка загрузки расписания path=%s',
            __name__,
            exc_info=error,
        )
        return

    data_tr_schedules: dict[str, list[int]] = {
        tr_schedule.date.isoformat(): _split_time(tr_schedule.time)
        for tr_schedule in trainer_schedules
    }

    for schedule in schedules:  # Schedule
        schedule_schema: ScheduleSchema = ScheduleSchema(**schedule.get_data())
        iso_date: str = schedule_schema.date.isoformat()
        if iso_date in data_tr_schedules:
            if schedule_schema.time in data_tr_schedules[iso_date]:
                data_tr_schedules[iso_date].remove(
                    schedule_schema.time
                )
                if not data_tr_schedules[iso_date]:
                    data_tr_schedules.pop(iso_date)

    return data_tr_schedules


async def set_calendar(
    callback: CallbackQuery,
    widget: Button | ManagedCalendar,
    dialog_manager: DialogManager
) -> None:
    """
    Подготавливает виджет календаря согласно расписания тренера.
    """

    data_schedules: dict[str, list[int]] | None = \
        await _update_calendar(dialog_manager)

    if data_schedules is None:
        await callback.answer(
            text='Не удалось получить расписание, попробуйте еще раз.',
            show_alert=True,
        )
        return

    dialog_manager.dialog_data[SELECTED_DATES] = data_schedules

    dialog_manager.dialog_data[MY_SIGN] = 0  # color mark day

    await _reset_radio(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager,
    )
    await dialog_manager.switch_to(
        state=ClientState.schedule,
        show_mode=ShowMode.EDIT,
    )


async def on_date_selected(
    callback: CallbackQuery,
    widget: ManagedCalendar,
    dialog_manager: DialogManager,
    clicked_date: date
) -> None:
    """
    Обработчик выбора даты в календаре. Выполняет проверку
    актуальности данных календаря, валидацию выбранной даты и
    переход к следующему шагу - записи на тренировку.
    """

    data_schedules: dict[str, list[int]] | None = \
        await _update_calendar(dialog_manager)
    if data_schedules is None:
        await callback.answer(
            text='Произошла ошибка, попробуйте еще раз.',
            show_alert=True,
        )
        return

    selected_dates: dict[str, list[int]] = \
        dialog_manager.dialog_data[SELECTED_DATES]

    if data_schedules != selected_dates:
        dialog_manager.dialog_data[SELECTED_DATES] = data_schedules
        await callback.answer(
            text='Данные календаря были изменены, '
            'попробуйте еще раз, пожалуйста',
            show_alert=True,
        )
    else:
        trainer_id: int = dialog_manager.start_data[TRAINER_ID]
        if clicked_date.isoformat() in selected_dates:
            workout: Workout | None = await update_workouts(
                callback=callback,
                dialog_manager=dialog_manager,
                trainer_id=trainer_id,
            )

            if workout is None:
                await callback.answer(
                    text='Неожиданая ошибка, попробуйте еще раз.',
                    show_alert=True,
                )
                return

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
    clicked_date: date
) -> None:
    """
    Обработчик выбора даты в календаре для отмены тренировок.
    Проверяет актуальность данных и переходит к процессу
    отмены выбранной тренировки.
    Валидация выбранной даты, проверка наличия у клиента записей
    на эту дату и инициализация процесса отмены.
    """

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_datetime(timezone)

    client_id: int = dialog_manager.event.from_user.id
    trainer_id: int = dialog_manager.start_data[TRAINER_ID]

    schedules: list[Schedule] = await _get_trainings(
        client_id=client_id,
        trainer_id=trainer_id,
        dialog_manager=dialog_manager,
    )

    if schedules is None:
        await callback.answer(
            text='Произошла ошибка, попробуйте еще раз.',
            show_alert=True,
        )
        return

    data_schedules: dict[str, list[int]] = _update_schedules(schedules)
    selected_dates: dict[str, list[int]] = \
        dialog_manager.dialog_data[SELECTED_DATES]

    if data_schedules != selected_dates:
        await callback.answer(
            text='Данные устарели, попробуйте еще раз.',
            show_alert=True,
        )
        await set_calendar(
            callback=callback,
            widget=widget,
            dialog_manager=dialog_manager,
        )
        return

    if clicked_date.isoformat() in dialog_manager.dialog_data[SELECTED_DATES]:
        dialog_manager.dialog_data[SELECTED_DATE] = \
            clicked_date.isoformat()

        if clicked_date == today.date():
            await dialog_manager.switch_to(
                state=ClientState.today,
                show_mode=ShowMode.EDIT,
            )
            return

        await dialog_manager.switch_to(
            state=ClientState.cancel_training,
            show_mode=ShowMode.EDIT,
        )


async def clear_data(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
) -> None:
    """
    Очищает данные о расписании и переходит на
    начальную страницу.
    """

    dialog_manager.dialog_data.clear()


async def _reset_radio(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Устанавливает переключатель радио в начальное положение.
    """

    radio: ManagedRadio = dialog_manager.find(RAD_SCHED)

    await radio.set_checked(0)


async def exist_sign(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Асинхронная функция для обработки записи клиента на тренировку.
    Проверка доступности времени у тренера,
    создание записи на тренировку и настройка напоминания для клиента.
    """

    context: Context = dialog_manager.current_context()

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_datetime(timezone)

    radio_item: str = context.widget_data.get(RAD_SCHED)

    client_id: int = dialog_manager.event.from_user.id
    trainer_id: int = dialog_manager.start_data[TRAINER_ID]
    selected_date: str = dialog_manager.dialog_data[SELECTED_DATE]
    selected_dates: dict[str, list[int]] = \
        dialog_manager.dialog_data[SELECTED_DATES]
    selected_time: int = selected_dates[selected_date][int(radio_item)]
    dialog_manager.dialog_data[EXIST] = False

    if selected_date <= today.date().isoformat():
        await callback.answer(
            text='Данные устарели, попробуйте еще раз.',
            show_alert=True,
        )
        await set_calendar(
            callback=callback,
            widget=widget,
            dialog_manager=dialog_manager,
        )
        return

    exists_schedule: bool
    trainer_schedule: TrainerSchedule

    try:
        exists_schedule, trainer_schedule = await asyncio.gather(
            get_schedule_exsists(
                dialog_manager=dialog_manager,
                selected_date=selected_date,
                selected_time=selected_time,
                trainer_id=trainer_id,
            ),
            get_trainer_schedule(
                dialog_manager=dialog_manager,
                trainer_id=trainer_id,
                selected_date=selected_date,
            )
        )
    except SQLAlchemyError as error:
        logger.error(
            'Ошибка проверки существования записи и извлечения '
            'списка расписания тренера trainer_id=%s, client_id=%s, '
            'selected_date=%s, selected_time=%s, path=%s',
            trainer_id, client_id, selected_date, selected_time,
            __name__,
            exc_info=error,
        )
        await callback.answer(
            text='Неудалось записать вас на тренировку, '
                 'попробуйте еще раз.',
            show_alert=True,
        )
        return

    if not exists_schedule:
        if trainer_schedule is not None:
            trainer_times: list[str] = trainer_schedule.time.split(',')
            if str(selected_time) in trainer_times:
                try:
                    schedule: Schedule | None = await add_training(
                        dialog_manager=dialog_manager,
                        selected_date=selected_date,
                        selected_time=selected_time,
                        client_id=client_id,
                        trainer_id=trainer_id,
                    )
                except SQLAlchemyError as error:
                    logger.error(
                        'Ошибка при попытке записаться на тренировку '
                        'trainer_id=%s, client_id=%s, date=%s, '
                        'time=%s, path=%s',
                        trainer_id, client_id, selected_date,
                        selected_time, __name__,
                        exc_info=error,
                    )
                    await callback.answer(
                        text='Во время записи произошла ошибка, '
                             'попробуйте еще раз.',
                        show_alert=True,
                    )
                    return

                if schedule is None:
                    await callback.answer(
                        text='Неудалось завершить запись, попробуйте '
                             'еще раз.',
                        show_alert=True,
                    )
                    return

                dialog_manager.dialog_data[EXIST] = True
                dialog_manager.start_data[WORKOUTS] -= 1

                datetime_notification = datetime.combine(
                    date=date.fromisoformat(selected_date)-timedelta(days=1),
                    time=time(hour=11, minute=00),
                    tzinfo=ZoneInfo(timezone),
                )

                if datetime_notification > today:

                    message = (
                        f'Напоминание о тренировке '
                        f'{selected_date} в {selected_time}:00'
                    )

                    sch_id = f'{client_id}_{selected_date}_{selected_time}'
                    kw = {'chat_id': client_id, 'message_text': message}
                    await schedule_source.add_schedule(
                        ScheduledTask(
                            task_name=send_scheduled_notification.task_name,
                            labels={},
                            args=[],
                            kwargs=kw,
                            schedule_id=sch_id,
                            time=datetime_notification,
                        )
                    )

                    logger.info(
                        'Задача об упоминании о тренировке запланирована '
                        'на дату <%s>, время <%s>',
                        datetime_notification.date().isoformat(),
                        datetime_notification.time().isoformat()
                    )

    await dialog_manager.switch_to(
        state=ClientState.sign_up,
        show_mode=ShowMode.EDIT,
    )


async def _get_trainings(
    client_id: int,
    trainer_id: int,
    dialog_manager: DialogManager
) -> list[Schedule] | None:
    """
    Функция для получения списка тренировок клиента.
    """

    try:
        schedules: list[Schedule] = await get_client_trainings(
            dialog_manager=dialog_manager,
            trainer_id=trainer_id,
            client_id=client_id,
        )
    except SQLAlchemyError as error:
        logger.error(
            'Ошибка при попытке получить список записей '
            'на тренировки клиента client_id=%s, trainer_id=%s, '
            'path=%s',
            client_id, trainer_id, __name__,
            exc_info=error,
        )
        return

    return schedules


def _update_schedules(
    schedules: list[Schedule]
) -> dict[str, list[int]]:
    """
    Вспомогательная синхронная функция для преобразования списка
    объектов Schedule в словарь, сгруппированный по датам.
    """

    data_schedules = {}

    for schedule in schedules:
        data_schedules.setdefault(schedule.date.isoformat(), [])\
            .append(schedule.time)

    return data_schedules


async def set_trainings(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager,
) -> None:
    """
    Функция для подготовки и отображения списка записей клиента на тренировки.
    Получение списка будущих тренировок клиента, преобразование данных в
    формат для отображения и переход в состояние просмотра "Мои записи".
    """

    client_id: int = dialog_manager.event.from_user.id
    trainer_id: int = dialog_manager.start_data[TRAINER_ID]

    schedules: list[Schedule] | None = await _get_trainings(
        client_id=client_id,
        trainer_id=trainer_id,
        dialog_manager=dialog_manager,
    )

    if schedules is None:
        await callback.answer(
            text='Произошла неожиданная ошибка, попробуйте еще раз.',
            show_alert=True,
        )
        return

    if not schedules:
        await callback.answer(
            text='У вас нет записей.',
            show_alert=True,
        )

    selected_dates: dict[str, list[int]] = _update_schedules(schedules)
    dialog_manager.dialog_data[SELECTED_DATES] = selected_dates

    dialog_manager.dialog_data[MY_SIGN] = 1
    await dialog_manager.switch_to(
        state=ClientState.my_sign_up,
        show_mode=ShowMode.EDIT,
    )


async def _reset_widget(
    dialog_manager: DialogManager
) -> None:
    """
    Находит виджет множественного выбора по идентификатору и
    сбрасывает его выбранные элементы.
    """

    multiselect: ManagedMultiselect = dialog_manager.find(SEL_D)
    await multiselect.reset_checked()


async def back_trainings(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Возврат к окну записей тренировок клиента.
    """

    await _reset_widget(dialog_manager=dialog_manager)

    await set_trainings(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager,
    )


async def cancel_training(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_datetime(timezone)

    context: Context = dialog_manager.current_context()

    selected_date: str = dialog_manager.dialog_data[SELECTED_DATE]
    client_id: int = dialog_manager.event.from_user.id
    trainer_id: int = dialog_manager.start_data[TRAINER_ID]

    if today.date().isoformat() < selected_date:

        times: list[int] = \
            dialog_manager.dialog_data[SELECTED_DATES][selected_date]
        widget_items = list(map(int, context.widget_data.get(SEL_D)))

        canceling_times: list[int] = [
            {
                'client_id': client_id,
                'time': times[item]
            } for item in widget_items
        ]

        try:
            result: list[dict[str, Schedule | Workout]] = \
                await cancel_training_db(
                    dialog_manager=dialog_manager,
                    selected_date=selected_date,
                    trainer_id=trainer_id,
                    trainings=canceling_times,
                )
        except SQLAlchemyError as error:
            logger.error(
                'Ошибка отмены записи клиентом client_id=%s, '
                'trainer_id=%s, date=%s, path=%s',
                client_id, trainer_id, selected_date, __name__,
                exc_info=error,
            )
            await callback.answer(
                text='Произошла неожиданая ошибка, попробуйте еще раз.',
                show_alert=True,
            )
            return
        if result is None:
            await callback.answer(
                text='Неудалось отменить ваши записи, попробуйте '
                     'еще раз.',
                show_alert=True,
            )
            return

        client_name: str = dialog_manager.event.from_user.full_name
        schedule: Schedule
        workout: Workout
        for row in result:
            schedule, workout = row.values()
            message = (
                f'❌{client_name} отменил(а) запись: '
                f'{schedule.date.isoformat()}, {schedule.time}:00'
            )
            await send_notification(
                bot=dialog_manager.event.bot,
                user_id=trainer_id,
                text=message,
            )

            schedule_task_id = (
                f'{client_id}_'
                f'{schedule.date.isoformat()}_'
                f'{schedule.time}'
            )
            await schedule_source.delete_schedule(schedule_task_id)

            logger.info(
                'Задача об уведомлении id=%s отменена', schedule_task_id
            )
        dialog_manager.start_data[WORKOUTS] = workout.workouts
        dialog_manager.dialog_data[SELECTED_DATES].pop(selected_date)

        await _reset_widget(dialog_manager=dialog_manager)

    else:

        await callback.answer(
            text='Данные устарели, попробуйте еще раз, пожалуйста.',
            show_alert=True,
        )

    await set_trainings(
        callback=callback,
        widget=widget,
        dialog_manager=dialog_manager,
    )
