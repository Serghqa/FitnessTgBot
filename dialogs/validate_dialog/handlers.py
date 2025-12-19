import asyncio
import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode, ShowMode
from aiogram_dialog.api.entities.context import Context
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import ManagedTextInput
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError
from string import ascii_lowercase, digits
from typing import Callable

from config import load_config, Config
from db import (
    add_client,
    add_trainer,
    add_workout,
    Client,
    get_trainers,
    get_user,
    get_workouts,
    relation_exists_trainer_client,
    set_client,
    set_trainer,
    set_workout,
    Trainer,
    Workout,
)
from notification import send_notification
from schemas import ClientSchema, TrainerSchema
from states import ClientState, StartSG, TrainerState


logger = logging.getLogger(__name__)

ID = 'id'
NAME = 'name'
SIMBOLS = ascii_lowercase + digits
RADIO_GROUP = 'radio_group'
RADIO_TZ = 'radio_tz'
SESSION = 'session'
TIME_ZONE = 'time_zone'
TRAINERS = 'trainers'
TRAINER_ID = 'trainer_id'
WORKOUTS = 'workouts'


async def to_trainer_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Переключает диалог в режим тренера, используя данные тренера,
    ранее сохранённые в `dialog_manager.start_data`.
    """

    trainer_schema: TrainerSchema = TrainerSchema.model_validate(
        dialog_manager.start_data
    )

    await dialog_manager.start(
        data=trainer_schema.model_dump(),
        state=TrainerState.main,
        mode=StartMode.RESET_STACK,
    )


async def to_client_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
) -> None:
    """
    Переключает диалог в состояние выбора группы (тренера) для клиента.
    Загружает список тренеров, связанных с клиентом, и сохраняет их в
    `dialog_manager.dialog_data`. Если загрузка не удалась, выводит
    соответствующее сообщение об ошибке.
    """

    try:
        trainers: list[Trainer] | None = await get_trainers(dialog_manager)
    except SQLAlchemyError as error:
        logger.error(
            'При попытке получить список Trainer связанных с '
            'клиентом client_id=%s, произошла ошибка. '
            'path=%s',
            dialog_manager.event.from_user.id, __name__,
            exc_info=error,
        )
        await callback.answer(
            text='Ошибка, обратитесь в поддержку.',
            show_alert=True,
        )
        return

    if trainers is None:
        logger.error(
            'Не удалось загрузить данные Client. '
            'client_id=%s, path=%s',
            dialog_manager.event.from_user.id, __name__,
        )
        await callback.answer(
            text='Не удалось получить ваши данные. '
                 'Обратитесь в службу поддержки.',
            show_alert=True,
        )

    elif not trainers:
        logger.error(
            'Не удалось получить список Trainer связанный '
            'с клиентом client_id=%s, path=%s',
            dialog_manager.event.from_user.id, __name__,
        )
        await callback.answer(
            text='У вас нет ни одной группы. Обратитесь в службу поддержки.',
            show_alert=True,
        )

    else:
        dialog_manager.dialog_data[TRAINERS] = \
            [trainer.get_data() for trainer in trainers]

        await dialog_manager.switch_to(
            state=StartSG.group,
            show_mode=ShowMode.EDIT,
        )


async def on_trainer(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):
    """
    Обрабатывает выбор тренера клиентом через интерфейс,
    загружает данные о количестве тренировок клиента с этим тренером и
    переключает диалог в главное состояние клиента.

    В случае, если данные о тренировках не найдены или произошла ошибка,
    пользователю выводится сообщение об ошибке и диалог переключается
    на главное меню.
    """

    context: Context = dialog_manager.current_context()

    radio_checked: str = context.widget_data.get(RADIO_GROUP)

    trainer: dict = \
        dialog_manager.dialog_data[TRAINERS][int(radio_checked)]
    trainer_schema: TrainerSchema = TrainerSchema.model_validate(trainer)

    try:
        workout_db: Workout = await get_workouts(
            dialog_manager=dialog_manager,
            trainer_id=trainer_schema.id,
            client_id=dialog_manager.event.from_user.id,
        )
    except SQLAlchemyError as error:
        logger.error(
            'Ошибка при попытке получить Workout клиента '
            'client_id=%s, trainer_id=%s, path=%s',
            dialog_manager.event.from_user.id, trainer_schema.id, __name__,
            exc_info=error,
        )
        await callback.answer(
            text='Произошла неожиданная ошибка, попробуйте еще раз '
                 'или обратитесь в поддержку.',
            show_alert=True,
        )
        return

    if workout_db is None:
        logger.error(
            'Не удалось загрузить количество тренировок '
            'клиента client_id=%s, trainer_id=%s',
            dialog_manager.event.from_user.id, trainer_schema.id,
        )
        await callback.answer(
            text='Не удалось загрузить количество ваших тренировок. '
                 'Обратитесь в службу поддержки, пожалуйста.',
            show_alert=True,
        )
        await dialog_manager.switch_to(
            state=StartSG.main,
            show_mode=ShowMode.EDIT,
        )
    else:
        client_schema: ClientSchema = ClientSchema(
            id=dialog_manager.start_data[ID],
            name=dialog_manager.start_data[NAME],
            workouts=workout_db.workouts,
        )

        dialog_manager.start_data.clear()

        client_data: dict = _set_client_data(
            client_id=client_schema.id,
            client_name=client_schema.name,
            trainer_id=trainer_schema.id,
            time_zone=trainer_schema.time_zone,
            workouts=client_schema.workouts,
        )

        await dialog_manager.start(
            data=client_data,
            state=ClientState.main,
            mode=StartMode.RESET_STACK,
        )


def trainer_validate(type_factory: Callable):

    config: Config = load_config()

    @wraps(type_factory)
    def wrapper(code: str):

        if code != config.tg_bot.IS_TRAINER:
            raise ValueError
        result = type_factory(code)
        return result

    return wrapper


@trainer_validate
def is_trainer(code: str) -> str:

    return code


def is_client(code: str) -> str:

    if code.isdigit():
        return code

    raise ValueError


async def trainer_is_valid(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str
):

    await message.delete()

    await dialog_manager.switch_to(
        state=StartSG.set_tz,
        show_mode=ShowMode.EDIT,
    )


async def error_code(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    error: ValueError
):

    await message.answer(text='Неверный код')


async def client_is_valid(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str
):
    """
    Обрабатывает ввод номера группы (тренера) клиентом.
    Если номер действителен, добавляет клиента к указанному тренеру,
    отправляет уведомление тренеру и переключает диалог в главное
    состояние клиента.
    Если номер недействителен или произошла ошибка при добавлении,
    отправляет соответствующее сообщение об ошибке.
    """

    await message.delete()

    trainer_id = int(text)
    client_id = dialog_manager.event.from_user.id
    client_data = {}

    try:
        relation_client_trainer: bool = \
            await relation_exists_trainer_client(
                dialog_manager=dialog_manager,
                client_id=client_id,
                trainer_id=trainer_id,
            )
        if relation_client_trainer:
            await message.answer(
                text='Вы уже состоите в данной группе'
            )
            await dialog_manager.update(
                dialog_manager.dialog_data,
                show_mode=ShowMode.SEND
            )
            await dialog_manager.switch_to(
                state=StartSG.group,
                show_mode=ShowMode.EDIT,
            )
            return

        client_schema: ClientSchema = ClientSchema(
            id=client_id,
            name=dialog_manager.event.from_user.full_name
        )
        workout: Workout = set_workout(
            trainer_id=trainer_id,
            workouts=0,
            client_id=client_id,
        )

        client_db: Client | None
        trainer_db: Trainer | None

        trainer_db, client_db = await asyncio.gather(
            get_user(
                dialog_manager=dialog_manager,
                user_id=trainer_id,
                model=Trainer,
            ),
            get_user(
                dialog_manager=dialog_manager,
                user_id=client_id,
                model=Client,
            )
        )

        if trainer_db is None:
            await message.answer(
                text='Неверный номер группы, попробуйте еще раз, пожалуйста!',
            )
            return

        if client_db is None:
            client: Client = set_client(
                id=client_schema.id,
                name=client_schema.name,
            )

            client_db: Client = await add_client(
                dialog_manager=dialog_manager,
                trainer=trainer_db,
                client=client,
                workout=workout,
            )
            client_data: dict = _set_client_data(
                client_id=client_db.id,
                client_name=client_db.name,
                trainer_id=trainer_db.id,
                time_zone=trainer_db.time_zone,
                workouts=workout.workouts,
            )

        else:
            await add_workout(
                dialog_manager=dialog_manager,
                workout=workout,
            )
            client_data: dict = _set_client_data(
                client_id=client_schema.id,
                client_name=client_schema.name,
                trainer_id=trainer_db.id,
                time_zone=trainer_db.time_zone,
                workouts=workout.workouts,
            )
    except SQLAlchemyError as error:
        logger.error(
            'Ошибка при попытке вступить в группу, '
            'trainer_id=%s, client_id=%s, path=%s',
            trainer_id, client_id, __name__,
            exc_info=error,
        )
        await message.answer(
            text='Произошла неожиданная ошибка, '
                 'обратитесь в службу поддержки.'
        )
        return

    text = f'Клиент {client_schema.name} присоединился к группе'
    await send_notification(
        bot=dialog_manager.event.bot,
        user_id=trainer_id,
        text=text,
    )

    await dialog_manager.start(
        data=client_data,
        state=ClientState.main,
        mode=StartMode.RESET_STACK,
    )


def _set_client_data(
    client_id: int,
    client_name: str,
    trainer_id: int,
    time_zone: str,
    workouts: int
) -> dict:

    data = {
        'client_id': client_id,
        'client_name': client_name,
        'trainer_id': trainer_id,
        'time_zone': time_zone,
        'workouts': workouts
    }

    return data


async def apply_tz(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):
    """
    Сохраняет выбранный часовой пояс тренера, добавляет данные тренера в
    систему и переключает диалог в главное состояние тренера.
    В случае ошибки — выводит уведомление и возвращает в главное меню.
    """

    context: Context = dialog_manager.current_context()
    local_zone: str = context.widget_data.get(RADIO_TZ)

    trainer_schema: TrainerSchema = TrainerSchema(
        id=dialog_manager.event.from_user.id,
        name=dialog_manager.event.from_user.full_name or 'no_name',
        time_zone=local_zone,
    )
    trainer: Trainer = set_trainer(
        id=trainer_schema.id,
        name=trainer_schema.name,
        time_zone=trainer_schema.time_zone,
    )

    try:
        await add_trainer(
            trainer=trainer,
            dialog_manager=dialog_manager,
        )
    except SQLAlchemyError as error:
        logger.error(
            'Произошла ошибка при попытке добавить Trainer '
            'в базу данных trainer_id=%s, path=%s',
            trainer_schema.id, __name__,
            exc_info=error,
        )
        await callback.answer(
            text='Не удалось дабавить ваши данные, попробуйте еще раз или '
                 'обратитесь в службу поддержки, пожалуйста.',
            show_alert=True,
        )
        await dialog_manager.switch_to(
            state=StartSG.main,
            show_mode=ShowMode.EDIT,
        )
        return

    await dialog_manager.start(
        data=trainer_schema.model_dump(),
        state=TrainerState.main,
        mode=StartMode.RESET_STACK,
    )
