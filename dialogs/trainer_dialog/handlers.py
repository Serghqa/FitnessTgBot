import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select, ManagedRadio
from aiogram_dialog.widgets.input import MessageInput
from sqlalchemy.orm import Session
from states.trainer_states import TrainerState
from db import get_trainer


logger = logging.getLogger(__name__)


async def to_group_window(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):
    trainer_id = dialog_manager.start_data.get('id')
    session: Session = dialog_manager.middleware_data.get('session')
    group: list = get_trainer(session, trainer_id, trainer_id).get('group')
    data = {'group': group, 'frame': {'start': 0, 'step': 3}}
    dialog_manager.dialog_data['data'] = data
    await dialog_manager.switch_to(state=TrainerState.group)


async def to_main_trainer_window(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):
    await dialog_manager.switch_to(state=TrainerState.main)


async def on_client(
        callback: CallbackQuery,
        widget: Select,
        dialog_manager: DialogManager,
        item_id: str
):
    print(item_id)


async def to_message_window(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):
    await dialog_manager.switch_to(state=TrainerState.message)


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
