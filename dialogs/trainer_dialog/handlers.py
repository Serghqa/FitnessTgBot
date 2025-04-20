import logging

from typing import Any
from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button, Select, ManagedRadio
from aiogram_dialog.widgets.input import MessageInput
from states import TrainerState, ClientEditState
from db import Trainer, get_data_user
from test import test_trainer_true, test_group_true, test_not_data


logger = logging.getLogger(__name__)


async def to_group_window(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    test_trainer_true(dialog_manager.start_data)  # test the trainer must be True
    test_not_data(dialog_manager.dialog_data)  # test dialog_data must be empty

    FRAME = {'start': 0, 'step': 3}
    user_data = get_data_user(dialog_manager, Trainer, True)
    user_data['frame'] = FRAME

    dialog_manager.dialog_data.update(user_data)

    test_group_true(dialog_manager.dialog_data)  # test group is list[dict]

    await dialog_manager.switch_to(
        state=TrainerState.group,
        show_mode=ShowMode.EDIT
    )


async def to_main_trainer_window(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    dialog_manager.dialog_data.clear()

    test_not_data(dialog_manager.dialog_data)  # test dialog_data is empty

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

    client_data: dict[str, Any] = dialog_manager.dialog_data['group'][int(item_id)]
    client_data['workout'] = 0

    await dialog_manager.start(
        state=ClientEditState.main,
        data=client_data,
        show_mode=ShowMode.EDIT
    )


async def to_message_window(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):

    test_not_data(dialog_manager.dialog_data)  # test dialog_data is empty

    dialog_manager.dialog_data['send_all'] = True

    await dialog_manager.switch_to(
        state=TrainerState.message,
        show_mode=ShowMode.EDIT
    )


async def send_message(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager
):

    send_all = dialog_manager.dialog_data.get('send_all')

    group = get_data_user(dialog_manager, Trainer, True).get('group')
    for client in group:
        if client['workouts'] or send_all:
            print(client)


async def process_selection(
        callback: CallbackQuery,
        widget: ManagedRadio,
        dialog_manager: DialogManager,
        item_id: str
):

    dialog_manager.dialog_data['send_all'] = item_id == '1'


async def set_radio_default(
    _,
    dialog_manager: DialogManager
):

    radio: ManagedRadio = dialog_manager.find('send_checked')
    await radio.set_checked('1')
