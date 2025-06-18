import logging

from aiogram.types import CallbackQuery, Message

from aiogram_dialog import DialogManager, StartMode
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button

from typing import Callable
from functools import wraps
from string import ascii_lowercase, digits
#  from config import load_config, Config

from states import trainer_states, client_states
from db import add_client, add_trainer, get_data_user, Client


logger = logging.getLogger(__name__)

SIMBOLS = ascii_lowercase + digits
TRAINER = 'trainer'
TRAINER_ID = 'trainer_id'
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
        state=trainer_states.TrainerState.main,
        mode=StartMode.RESET_STACK,
    )


async def to_client_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    data_preparation(dialog_manager.start_data)

    await dialog_manager.start(
        data=dialog_manager.start_data,
        state=client_states.ClientState.main,
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

    data: dict = set_data_user(dialog_manager)
    await add_trainer(data[ID], data[NAME], dialog_manager)

    await dialog_manager.start(
        data=data,
        state=trainer_states.TrainerState.main,
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
    
    data: dict = set_data_user(dialog_manager)

    trainer_id = int(text)
    await add_client(dialog_manager, trainer_id)

    data[TRAINER_ID] = trainer_id
    data[WORKOUTS] = 0

    await dialog_manager.start(
        data=data,
        state=client_states.ClientState.main,
        mode=StartMode.RESET_STACK
    )
