import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode, ShowMode
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button
from sqlalchemy.orm import Session
from typing import Callable
from functools import wraps
from string import ascii_lowercase, digits
#  from config import load_config, Config
from states import start_states, trainer_states, client_states
from db import Trainer, Client, add_trainer_db, add_client_db, get_data_user
from tmp_db import data_base


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

    session: Session = dialog_manager.middleware_data.get('session')
    trainer_id = dialog_manager.event.from_user.id

    user_data = get_data_user(session, trainer_id, Trainer)

    await dialog_manager.start(
        data=user_data,
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


def get_valid_variable(type_factory: Callable):
    #  config: Config = load_config()

    @wraps(type_factory)
    def wrapper(code: str):
        #  if code != config.tg_bot.IS_TRAINER:
        #    raise ValueError
        result = type_factory(code)
        return result

    return wrapper


@get_valid_variable
def valid_code(code: str) -> str:

    return code


def is_valid_client(code: str) -> str:

    if code in data_base['trainers']:
        return code

    raise ValueError


async def successful_code(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str
):

    trainer_id = message.from_user.id
    name = message.from_user.full_name
    session: Session = dialog_manager.middleware_data.get('session')
    
    add_trainer_db(session, trainer_id, name)
    ids = [123456780, 123654789, 456789123, 159753654, 456369852, 456369855]
    names = ['sedhh', 'hgvghd', 'hjgtd', 'ghfgcxfdxf', 'ghcfgxdf', 'fvccszsd']
    for i in range(len(ids)):
        add_client_db(session, ids[i], names[i], trainer_id)

    user_data = get_data_user(session, trainer_id, Trainer)

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

    trainer_id = text
    client_id = str(message.from_user.id)
    data_base['trainers'][trainer_id].update({client_id: {}})
    data_base['clients'][client_id] = trainer_id
    await dialog_manager.start(
        state=client_states.ClientState.main,
        mode=StartMode.RESET_STACK
    )
