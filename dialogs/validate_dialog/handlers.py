import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode, ShowMode
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button
from typing import Callable
from functools import wraps
from string import ascii_lowercase, digits
#  from config import load_config, Config
from states import start_states, trainer_states, client_states
from db import Trainer, add_user, get_data_user
from test import test_data_all_none, test_trainer_true


logger = logging.getLogger(__name__)
simbols = ascii_lowercase + digits


async def is_trainer(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):

    await dialog_manager.switch_to(
        state=start_states.StartSG.trainer_validate,
        show_mode=ShowMode.EDIT
    )


async def to_trainer_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    test_trainer_true(dialog_manager.start_data)  # test the trainer must be True

    await dialog_manager.start(
        data=dialog_manager.start_data,
        state=trainer_states.TrainerState.main,
        mode=StartMode.RESET_STACK
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
        mode=StartMode.RESET_STACK
    )


async def to_main_start_window(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):

    await dialog_manager.switch_to(
        state=start_states.StartSG.start,
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
def is_valid_trainer(code: str) -> str:

    return code


def is_valid_client(code: str) -> str:

    if code.isdigit():
        return code

    raise ValueError


async def successful_code(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str
):

    test_data_all_none(dialog_manager.dialog_data)  # test the values ​​of all attributes must be None

    add_user(dialog_manager)
    add_user(dialog_manager, dialog_manager.event.from_user.id)  # для отладки
    user_data = get_data_user(dialog_manager, Trainer)

    test_trainer_true(user_data)  # test the trainer must be True
    #  add_user(dialog_manager, dialog_manager.event.from_user.id)  # для отладки

    await dialog_manager.start(
        data=user_data,
        state=trainer_states.TrainerState.main,
        mode=StartMode.RESET_STACK
    )


async def error_code(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError
):

    await message.answer(text='Error code')


async def successful_client_code(
    message: Message,
    widget: ManagedTextInput,
    dialog_manager: DialogManager,
    text: str
):

    trainer_id = int(text)
    add_user(dialog_manager, trainer_id)

    await dialog_manager.start(
        state=client_states.ClientState.main,
        mode=StartMode.RESET_STACK
    )
