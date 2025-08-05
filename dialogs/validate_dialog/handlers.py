import logging

from aiogram.types import CallbackQuery, Message

from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.api.entities.context import Context

from faker import Faker
from typing import Callable
from functools import wraps
from string import ascii_lowercase, digits
#  from config import load_config, Config

from states import TrainerState, ClientState, trainer_states, client_states
from db import add_client, add_trainer, get_data_user, Trainer, Workout, get_trainers, get_workouts


logger = logging.getLogger(__name__)

SIMBOLS = ascii_lowercase + digits
TRAINER = 'trainer'
TRAINERS = 'trainers'
TRAINER_ID = 'trainer_id'
RADIO_GROUP = 'radio_group'
CLIENT = 'client'
ID = 'id'
NAME = 'name'
WORKOUTS = 'workouts'


def data_preparation(data: dict) -> None:

    data.pop(CLIENT)
    data.pop(TRAINER)


def set_data_user(dialog_manager: DialogManager) -> dict:

    id = dialog_manager.event.from_user.id
    name = dialog_manager.event.from_user.full_name or 'no_name'

    return {ID: id, NAME: name}


async def to_trainer_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    data_preparation(dialog_manager.start_data)

    await dialog_manager.start(
        data=dialog_manager.start_data,
        state=TrainerState.main,
        mode=StartMode.RESET_STACK,
    )


async def to_client_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    trainers: list[Trainer] = await get_trainers(dialog_manager)
    dialog_manager.dialog_data[TRAINERS] = trainers

    data_preparation(dialog_manager.start_data)


async def on_trainer(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    context: Context = dialog_manager.current_context()

    radio_checked: str = context.widget_data.get(RADIO_GROUP)

    trainer: Trainer = dialog_manager.dialog_data[TRAINERS][int(radio_checked)]

    workout: Workout = await get_workouts(
        dialog_manager=dialog_manager,
        trainer_id=trainer.id,
        client_id=dialog_manager.event.from_user.id
    )

    dialog_manager.start_data[TRAINER_ID] = trainer.id
    dialog_manager.start_data[WORKOUTS] = workout.workouts

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

    user_data: dict = set_data_user(dialog_manager)

    await add_trainer(user_data[ID], user_data[NAME], dialog_manager)

    #УДАЛИТЬ
    fake = Faker(locale='ru_RU')
    for id in range(200_000_000, 200_000_100, 10):
        await add_trainer(id, str(id), dialog_manager)

        for i in range(10):
            await add_client(
                dialog_manager=dialog_manager,
                trainer_id=id,
                client_id=id+i,
                name=fake.name()
            )

    for id in range(200_000_100, 200_000_110):
        await add_client(
            dialog_manager=dialog_manager,
            trainer_id=user_data[ID],
            client_id=id,
            name=fake.name()
        )

    await dialog_manager.start(
        data=user_data,
        state=TrainerState.main,
        mode=StartMode.RESET_STACK
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

    user_data: dict = set_data_user(dialog_manager)

    trainer_id = int(text)
    try:
        await add_client(dialog_manager, trainer_id)

        user_data[TRAINER_ID] = trainer_id
        user_data[WORKOUTS] = 3

        await dialog_manager.start(
            data=user_data,
            state=ClientState.main,
            mode=StartMode.RESET_STACK
        )
    except ValueError:
        await message.answer(
            text='Неверный номер группы, попробуйте еще раз, пожалуйста!'
        )
