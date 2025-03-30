import logging

from aiogram.types import CallbackQuery, Update, Message
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button, Select, ManagedRadio
from aiogram_dialog.widgets.input import MessageInput
from typing import Any
from tmp_db import data_base
from states.trainer_states import TrainerState
from pprint import pprint


logger = logging.getLogger(__name__)


async def to_group_window(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):
    dialog_manager.dialog_data['frame'] = {'start': 0, 'step': 5}
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


#  -----Getters-----


async def get_data_group(dialog_manager: DialogManager, **kwargs):

    frame: dict[str, int] = dialog_manager.dialog_data.get('frame')
    start, step = frame.values()
    trainer_id = str(kwargs.get('event_from_user').id)
    group: list[tuple[str]] | None = data_base['trainers'].get(trainer_id)
    update: Update = kwargs.get('event_update')
    if update.callback_query:
        if update.callback_query.data.endswith('group_next'):
            if start + step < len(group):
                start = start + step
            else:
                start = 0
        elif update.callback_query.data.endswith('group_prev'):
            if start - step >= 0:
                start = start - step
        dialog_manager.dialog_data['frame']['start'] = start
    return {'trainer_id': trainer_id, 'group': group[start:start+step]}


async def message_data(dialog_manager: DialogManager, **kwargs):
    return {'radio': [('Всем', 1), ('Оплаченным', 2)]}
