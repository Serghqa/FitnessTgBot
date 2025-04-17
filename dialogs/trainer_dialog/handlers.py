import logging

from typing import Any
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button, Select, ManagedRadio
from aiogram_dialog.widgets.input import MessageInput
from sqlalchemy.orm import Session
from states import TrainerState, ClientEditState
from db import Trainer, get_data_user


logger = logging.getLogger(__name__)


async def to_group_window(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    FRAME = {'start': 0, 'step': 3}
    user_id = dialog_manager.event.from_user.id
    session: Session = dialog_manager.middleware_data.get('session')

    user_data = get_data_user(session, user_id, Trainer, True)

    dialog_manager.dialog_data.update(user_data)
    dialog_manager.dialog_data['frame'] = FRAME

    await dialog_manager.switch_to(
        state=TrainerState.group,
        show_mode=ShowMode.EDIT
    )


async def to_main_trainer_window(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await dialog_manager.switch_to(
        state=TrainerState.main,
        show_mode=ShowMode.EDIT
    )


async def on_client(
        callback: CallbackQuery,
        widget: Select,
        dialog_manager: DialogManager,
        item_id: str
):

    group_data: dict[str, Any] = dialog_manager.dialog_data['group'][int(item_id)]
    group_data['workout'] = 0

    await dialog_manager.start(
        state=ClientEditState.main,
        data=group_data,
        show_mode=ShowMode.EDIT
    )


async def to_message_window(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):

    await dialog_manager.switch_to(
        state=TrainerState.message,
        show_mode=ShowMode.EDIT
    )


async def send_message(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager
):

    print(type(message))


async def process_selection(
        callback: CallbackQuery,
        widget: ManagedRadio,
        dialog_manager: DialogManager,
        item_id: str
):

    print(item_id)


async def set_radio_default(
    _,
    dialog_manager: DialogManager
):

    radio: ManagedRadio = dialog_manager.find('send_checked')
    await radio.set_checked('1')
