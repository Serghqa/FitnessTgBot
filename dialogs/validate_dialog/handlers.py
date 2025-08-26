import logging

from aiogram.types import CallbackQuery, Message

from aiogram_dialog import DialogManager, StartMode, ShowMode
from aiogram_dialog.api.entities.context import Context
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import ManagedTextInput

from functools import wraps
from string import ascii_lowercase, digits
from typing import Callable

#  from config import load_config, Config
from db import (
    add_client,
    add_trainer,
    get_trainers,
    get_workouts,
    Trainer,
    Workout,
)
from send_message import send_message
from schemas import ClientSchema, TrainerSchema
from states import ClientState, StartSG, TrainerState


logger = logging.getLogger(__name__)

ID = 'id'
NAME = 'name'
SIMBOLS = ascii_lowercase + digits
TRAINERS = 'trainers'
TRAINER_ID = 'trainer_id'
RADIO_GROUP = 'radio_group'
WORKOUTS = 'workouts'


def set_user(
    dialog_manager: DialogManager,
    schema: ClientSchema | TrainerSchema
) -> ClientSchema | TrainerSchema:

    id = dialog_manager.event.from_user.id
    name = dialog_manager.event.from_user.full_name or 'no_name'

    schema: ClientSchema | TrainerSchema = schema(
        id=id,
        name=name,
    )

    return schema


async def to_trainer_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    trainer_schema: TrainerSchema = TrainerSchema(
        **dialog_manager.start_data
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
):

    trainers: list[Trainer] | None = await get_trainers(dialog_manager)

    if trainers is None:
        await callback.answer(
            text='Не получилось получить ваши данные. '
                 'Обратитесь в службу поддержки.',
            show_alert=True,
        )

    elif not trainers:
        await callback.answer(
            text='У вас нет ни одной группы. Обратитесь в службу поддержки.',
            show_alert=True,
        )

    else:
        dialog_manager.dialog_data[TRAINERS] = trainers

        await dialog_manager.switch_to(
            state=StartSG.group,
            show_mode=ShowMode.EDIT,
        )


async def on_trainer(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    context: Context = dialog_manager.current_context()

    radio_checked: str = context.widget_data.get(RADIO_GROUP)

    trainer_db: Trainer = \
        dialog_manager.dialog_data[TRAINERS][int(radio_checked)]
    trainer: TrainerSchema = TrainerSchema(**trainer_db.get_data())

    workout: Workout = await get_workouts(
        dialog_manager=dialog_manager,
        trainer_id=trainer.id,
        client_id=dialog_manager.event.from_user.id,
    )

    client: ClientSchema = ClientSchema(
        id=dialog_manager.start_data[ID],
        name=dialog_manager.start_data[NAME],
        workouts=workout.workouts,
    )

    dialog_manager.start_data.clear()
    dialog_manager.start_data[TRAINER_ID] = trainer.id
    dialog_manager.start_data.update(client.model_dump())

    await dialog_manager.start(
        data=dialog_manager.start_data,
        state=ClientState.main,
        mode=StartMode.RESET_STACK,
    )


def trainer_validate(type_factory: Callable):

    #  config: Config = load_config()

    @wraps(type_factory)
    def wrapper(code: str):

        #  if code != config.tg_bot.IS_TRAINER:
        #    raise ValueError
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

    trainer: TrainerSchema = set_user(
        dialog_manager=dialog_manager,
        schema=TrainerSchema,
    )

    await add_trainer(
        id=trainer.id,
        name=trainer.name,
        dialog_manager=dialog_manager,
    )

    await dialog_manager.start(
        data=trainer.model_dump(),
        state=TrainerState.main,
        mode=StartMode.RESET_STACK,
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

    client: ClientSchema = set_user(
        dialog_manager=dialog_manager,
        schema=ClientSchema,
    )
    trainer_id = int(text)

    try:
        await add_client(
            dialog_manager=dialog_manager,
            trainer_id=trainer_id,
            client_id=client.id,
            name=client.name,
        )

        text = f'Клиент {client.name} присоединился к группе'

        await send_message(
            dialog_manager=dialog_manager,
            user_id=client.id,
            text=text,
        )

        user_data: dict = client.model_dump()
        user_data[TRAINER_ID] = trainer_id
        user_data[WORKOUTS] = 0

        await dialog_manager.start(
            data=user_data,
            state=ClientState.main,
            mode=StartMode.RESET_STACK,
        )
    except ValueError:
        await message.answer(
            text='Неверный номер группы, попробуйте еще раз, пожалуйста!',
        )
