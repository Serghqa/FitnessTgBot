import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import Data, DialogManager, ShowMode
from aiogram_dialog.api.entities.context import Context
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.widgets.kbd import Button, ManagedRadio, Select, SwitchTo
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError
from typing import Literal

from db import (
    Client,
    get_client_db,
    get_frame_clients,
    get_work_days,
    get_workouts,
    WorkingDay,
    Workout,
)
from schemas import ClientSchema, WorkDaySchema
from states import ClientEditState, TrainerState, TrainerScheduleStates


logger = logging.getLogger(__name__)

GROUP = 'group'
ID = 'id'
WORKOUT = 'workout'
WORKOUTS = 'workouts'
OFFSET = 'offset'
LIMIT = 'limit'
RADIO_MESS = 'radio_mess'
RADIO_GROUP = 'radio_pag'
RADIO_WORK = 'radio_work'
SCHEDULES = 'schedules'
TIME_ZONE = 'time_zone'
WIDGET_DATA = 'widget_data'


def _get_current_widget_context(
    dialog_manager: DialogManager,
    key: str,
    default='1'
) -> Literal['1', '2', '3']:
    """
    Извлекает данные, связанные с определённым ключом, из текущего
    контекста виджета.
    """

    context: Context = dialog_manager.current_context()
    widget_data = context.widget_data.get(key, default)

    return widget_data


def exception_handling(func):
    @wraps(func)
    async def wrapper(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
    ):

        try:
            group: list[dict] = await func(
                callback,
                widget,
                dialog_manager,
            )
        except SQLAlchemyError as error:
            logger.error(
                'Ошибка пагинации для тренера '
                'trainer_id=%s, path=%s',
                dialog_manager.event.from_user.id, __name__,
                exc_info=error,
            )
            await callback.answer(
                text='Не получилось обновить данные.',
                show_alert=True,
            )
            group: list[dict] = dialog_manager.dialog_data.get(GROUP, [])

        dialog_manager.dialog_data[GROUP] = group
        return group
    return wrapper


async def get_client(
    message: Message,
    widget: MessageInput,
    dialog_manager: DialogManager
) -> None:
    """
    Обрабатывает ввод ID клиента, проверяет его корректность,
    ищет клиента в базе данных, связанного с текущим тренером.
    Если клиент найден, переключает диалог в режим редактирования клиента.
    """

    if not message.text:
        await message.answer('Ввели не корректные данные')

    elif message.text.isdigit():

        try:
            client_db: Client | None = await get_client_db(
                dialog_manager=dialog_manager,
                client_id=int(message.text),
                trainer_id=dialog_manager.event.from_user.id,
            )
        except SQLAlchemyError as error:
            logger.error(
                'Ошибка при попытке получить Client '
                'client_id=%s, trainer_id=%s, path=%s',
                int(message.text), dialog_manager.event.from_user.id, __name__,
                exc_info=error,
            )
            await message.answer(
                text='Возникла непредвиденная ошибка, попробуйте '
                     'еще раз или обратитесь в поддержку.'
            )
            return

        if client_db is not None:
            data_user = ClientSchema.model_validate(
                client_db.get_data()
            ).model_dump()
            for workout in client_db.workouts:
                if workout.trainer_id == dialog_manager.event.from_user.id:
                    data_user[WORKOUTS] = workout.workouts
                    data_user[WORKOUT] = 0
                    break

            await dialog_manager.start(
                state=ClientEditState.main,
                data=data_user,
                show_mode=ShowMode.EDIT,
            )

        else:
            await message.answer('Нет такого клиента')

    else:
        await message.answer('id должен состоять только из цифр')

    await message.delete()


async def _get_frame_group(
    dialog_manager: DialogManager,
    limit: int
) -> list[dict]:
    """
    Обновляет отображаемый список клиентов в диалоговом окне с
    учётом пагинации.
    """

    context: Context = dialog_manager.current_context()
    all: bool = context.widget_data.get(RADIO_GROUP) == '1'

    offset: int = dialog_manager.dialog_data[OFFSET]
    dialog_manager.dialog_data[OFFSET] += limit

    if dialog_manager.dialog_data[OFFSET] < 0:
        dialog_manager.dialog_data[OFFSET] = 0

    try:
        group: list[dict] = await get_frame_clients(
            dialog_manager=dialog_manager,
            all=all,
        )
        if not group and dialog_manager.dialog_data[OFFSET] > 0:
            dialog_manager.dialog_data[OFFSET] = 0
            group: list[dict] = await get_frame_clients(
                dialog_manager=dialog_manager,
                all=all,
            )
    except SQLAlchemyError as error:
        dialog_manager.dialog_data[OFFSET] = offset
        raise error

    return group


async def _set_radio_group(
    dialog_manager: DialogManager
) -> None:
    """
    Устанавливает состояние переключателя для группы управляемых переключателей
    на основе данных, полученных из контекста текущего виджета.
    """

    widget_item: Literal['1', '2', '3'] = \
        _get_current_widget_context(dialog_manager, RADIO_GROUP)

    radio: ManagedRadio = dialog_manager.find(RADIO_GROUP)
    await radio.set_checked(widget_item)


async def render_group(
    callback: CallbackQuery,
    widget: ManagedRadio,
    dialog_manager: DialogManager,
    item_id: str
) -> None:
    """
    Обрабатывает изменение выбора переключателя и обновляет отображение
    списка клиентов.
    """

    await widget.set_checked(item_id)
    await set_frame(callback, widget, dialog_manager)
    await dialog_manager.update(dialog_manager.dialog_data)


async def set_frame(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
) -> None:
    """
    Инициализирует данные пагинации и обновляет отображение
    фрейма списка клиентов.
    """

    dialog_manager.dialog_data.update(
        {
            OFFSET: 0,
            LIMIT: 5
        }
    )

    await _set_radio_group(dialog_manager)

    try:
        group: list[dict] = await _get_frame_group(dialog_manager, 0)
    except SQLAlchemyError as error:
        logger.error(
            'Ошибка при загрузке списка клиентов Client '
            'связанных с тренером trainer_id=%s, path=%s',
            dialog_manager.event.from_user.id, __name__,
            exc_info=error,
        )
        await callback.answer(
            text='При попытке получить список клиентов произошла '
                 'ошибка, попробуйте еще раз.',
            show_alert=True,
        )
        return

    dialog_manager.dialog_data[GROUP] = group
    await dialog_manager.switch_to(
        state=TrainerState.group,
        show_mode=ShowMode.EDIT,
    )


@exception_handling
async def next_page(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> list[dict]:
    """
    Обрабатывает переход на следующую страницу списка клиентов.
    """

    group: list[dict] = await _get_frame_group(
        dialog_manager,
        dialog_manager.dialog_data[LIMIT],
    )

    return group


@exception_handling
async def back_page(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> list[dict]:
    """
    Обрабатывает переход на предыдущую страницу списка клиентов.
    """

    group: list[dict] = await _get_frame_group(
        dialog_manager,
        -(dialog_manager.dialog_data[LIMIT]),
    )

    return group


async def to_main_window(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Переключает диалог в главное состояние тренера, очищая данные
    текущего диалога.
    """

    dialog_manager.dialog_data.clear()

    await dialog_manager.switch_to(
        state=TrainerState.main,
        show_mode=ShowMode.EDIT,
    )


async def on_client(
    callback: CallbackQuery,
    widget: Select,
    dialog_manager: DialogManager,
    item_id: str
) -> None:
    """
    Обрабатывает выбор клиента тренером из списка. Загружает актуальное
    количество тренировок клиента и переключает диалог в режим
    редактирования данных клиента.
    Если количество тренировок изменилось с момента последнего просмотра,
    выводит предупреждение.
    """

    data_client: dict = dialog_manager.dialog_data[GROUP][int(item_id)]

    client_schema: ClientSchema = ClientSchema.model_validate(data_client)

    try:
        workout: Workout = await get_workouts(
            dialog_manager=dialog_manager,
            trainer_id=dialog_manager.event.from_user.id,
            client_id=client_schema.id,
        )
    except SQLAlchemyError as error:
        logger.error(
            'Ошибка загрузки количества тренировок клиента '
            'client_id=%s, trainer_id=%s, path=%s',
            client_schema.id, dialog_manager.event.from_user.id, __name__,
            exc_info=error,
        )
        await callback.answer(
            text='Возникла ошибка при загрузке данных клиента.',
            show_alert=True,
        )
        return

    if workout is None:
        logger.warning(
            'Не удалось получить Workout клиента.'
            'client_id=%s, trainer_id=%s, path=%s',
            client_schema.id, dialog_manager.event.from_user.id, __name__,
        )
        await callback.answer(
            text='Произошла ошибка с загрузкой данных клиента, попробуйте еще '
            'раз или обратитесь в службу поддержки.',
            show_alert=True,
        )

    else:
        if workout.workouts != client_schema.workouts:
            client_schema.workouts = workout.workouts
            await callback.answer(
                text='Количество тренировок клиента было изменено.',
                show_alert=True,
            )
        data_client[WORKOUTS] = workout.workouts
        data_client[WORKOUT] = 0
        await dialog_manager.start(
            state=ClientEditState.main,
            data=data_client,
            show_mode=ShowMode.EDIT,
        )


async def to_schedule_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Переходит в диалог расписания тренера, передавая данные о рабочих днях
    и текущем выборе виджета.
    """

    widget_item: Literal['1', '2', '3'] = \
        _get_current_widget_context(dialog_manager, RADIO_WORK)

    try:
        work_days: list[WorkingDay] | None = \
            await get_work_days(dialog_manager)
    except SQLAlchemyError as error:
        logger.error(
            'Ошибка при загрузке списка WorkingDay тренера '
            'trainer_id=%s, path=%s',
            dialog_manager.event.from_user.id, __name__,
            exc_info=error,
        )
        await callback.answer(
            text='Произошла неожиданная ошибка, повторите еще раз.',
            show_alert=True,
        )
        return

    if work_days is not None:
        timezone: str = dialog_manager.start_data.get(TIME_ZONE)

        data = {SCHEDULES: {}, TIME_ZONE: timezone}

        for work_day in work_days:
            work_day_schema: WorkDaySchema = \
                WorkDaySchema.model_validate(work_day.get_data())
            item: str = work_day_schema.item  # '1' | '2' | '3'
            work: str = work_day_schema.work  # '10,11,12,13,14,'

            # SHEDULES = {'1': '10,11,12..', '2': '9,10,11..', '3': '12,13..'}
            data[SCHEDULES][item] = work

        # WIDGET_DATA = {'radio_work': '1' | '2' | '3'}
        data[WIDGET_DATA] = {RADIO_WORK: widget_item}

        await dialog_manager.start(
            data=data,
            state=TrainerScheduleStates.main,
            show_mode=ShowMode.EDIT,
        )

    else:
        logger.error(
            'Не удалось получить WorkDays тренера '
            'trainer_id=%s, path=%s',
            dialog_manager.event.from_user.id, __name__,
        )
        await callback.answer(
            text='Произошла ошибка, обратитесь в поддержку.',
            show_alert=True,
        )


async def process_result(
    start_data: Data,
    result: dict | None,
    dialog_manager: DialogManager
) -> None:
    """
    Обрабатывает результат, переданный из дочернего диалога.
    Если результат не пустой, обновляет данные текущего контекста виджета.
    """

    if result:
        context: Context = dialog_manager.current_context()
        context.widget_data.update(result)


async def update_result_group(
    start_data: Data,
    result: dict | None,
    dialog_manager: DialogManager
):
    """
    Обновляет данные клиента в группе (в `dialog_manager.dialog_data[GROUP]`)
    на основе результата, полученного из диалога client_edit_dialog.
    """

    client_id: int = result.get(ID)
    for client_data in dialog_manager.dialog_data.get(GROUP, []):
        if client_data.get(ID) == client_id:
            client_data.update(result)
            break
