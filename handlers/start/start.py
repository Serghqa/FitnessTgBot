import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode, ShowMode
from aiogram_dialog.widgets.input import MessageInput, ManagedTextInput
from aiogram_dialog.widgets.kbd import Button
from typing import Any, Callable
from functools import wraps
from string import ascii_lowercase, digits
from config import load_config, Config
from states import start_states, trainer_states, client_states
from tmp_db import data_base

logger = logging.getLogger(__name__)
simbols = ascii_lowercase + digits


#  -----Start handlers-----

async def is_trainer(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):
    await dialog_manager.switch_to(
        state=start_states.StartSG.trainer_validate,
        show_mode=ShowMode.DELETE_AND_SEND
    )


async def to_trainer_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):
    await dialog_manager.start(
        state=trainer_states.TrainerState.main,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.EDIT
    )


async def is_client(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):
    await dialog_manager.switch_to(
        state=start_states.StartSG.client_validate,
        show_mode=ShowMode.EDIT
    )


async def to_client_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):
    await dialog_manager.start(
        state=client_states.ClientState.main,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.EDIT
    )


#  -----Trainer validate handlers-----

async def cancel_is_trainer(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):
    await dialog_manager.switch_to(
        state=start_states.StartSG.start,
        show_mode=ShowMode.EDIT
    )


async def cancel_is_client(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):
    await dialog_manager.switch_to(
        state=start_states.StartSG.start,
        show_mode=ShowMode.EDIT
     )


def get_valid_variable(type_factory: Callable):
    config: Config = load_config()

    @wraps(type_factory)
    def wrapper(value: Any):
        result = type_factory(value, config)
        return result
    return wrapper


@get_valid_variable
def is_valid_code(value: Any, config: Config) -> str:
    if isinstance(value, str) and value == config.tg_bot.IS_TRAINER:
        return value
    raise ValueError


def is_valid_group_code(value: Any) -> str:
    if isinstance(value, str) and value in data_base['trainers']:
        return value
    raise ValueError


async def incorrect_data(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager
):
    await message.answer(text='Incorrect code')


async def correct_code(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str
):
    data_base['trainers'][str(message.from_user.id)] = {}
    await dialog_manager.start(
        state=trainer_states.TrainerState.main,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.EDIT
    )


async def error_code(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError
):
    await message.answer(text='Error code')


async def correct_group_code(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str
):
    trainer_id = text
    client_id = str(message.from_user.id)
    data_base['trainers'][trainer_id].update({client_id: {}})
    data_base['clients'][client_id] = trainer_id
    await dialog_manager.start(
        state=client_states.ClientState.main,
        mode=StartMode.RESET_STACK,
        show_mode=ShowMode.EDIT
    )


async def error_group_code(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    error: ValueError
):
    await message.answer(text='Error code')


#  -----Getters-----

async def get_data(**kwargs):
    user_id = str(kwargs['event_from_user'].id)
    is_trainer = user_id in data_base['trainers']
    is_client = user_id in data_base['clients']
    return {
        'user': is_trainer or is_client,
        'trainer': is_trainer,
        'client': is_client
    }
