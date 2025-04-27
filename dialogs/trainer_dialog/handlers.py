import logging

from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button, Select, ManagedRadio
from aiogram_dialog.widgets.input import MessageInput

from states import TrainerState, TrainerScheduleStates, ClientEditState
from db import Client, get_group, get_data_user


logger = logging.getLogger(__name__)


async def get_client(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager
):

    if not message.text:
        await message.answer('Ввели не корректные данные')

    elif message.text.isdigit():
        data = get_data_user(dialog_manager, Client, int(message.text))

        if data['client']:
            for user in dialog_manager.dialog_data['group']:
                if data['id'] == user['id']:
                    user['workout'] = 0

                    await dialog_manager.start(
                        state=ClientEditState.main,
                        data=user,
                        show_mode=ShowMode.SEND
                    )

                    break

        else:
            await message.answer('Нет такого клиента')

    else:
        await message.answer('id должен состоять только из цифр')


def _set_frame_group(dialog_manager: DialogManager, limit: int) -> None:

    dialog_manager.dialog_data['offset'] += limit

    if dialog_manager.dialog_data['offset'] < 0:
        dialog_manager.dialog_data['offset'] = 0

    group: list[dict] = get_group(dialog_manager)

    if not group:
        dialog_manager.dialog_data['offset'] = 0
        group: list[dict] = get_group(dialog_manager)

    dialog_manager.dialog_data['group'] = group


async def to_group_window(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    dialog_manager.dialog_data.update({'offset': 0, 'limit': 4})
    _set_frame_group(dialog_manager, 0)

    await dialog_manager.switch_to(
        state=TrainerState.group,
        show_mode=ShowMode.EDIT
    )


async def next_page(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    _set_frame_group(dialog_manager, dialog_manager.dialog_data['limit'])


async def back_page(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    _set_frame_group(dialog_manager, dialog_manager.dialog_data['limit'])


async def to_main_trainer_window(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    dialog_manager.dialog_data.clear()

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

    data: dict[str, Any] = dialog_manager.dialog_data['group'][int(item_id)]
    data['workout'] = 0

    await dialog_manager.start(
        state=ClientEditState.main,
        data=data,
        show_mode=ShowMode.EDIT
    )


async def to_schedule(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await dialog_manager.start(
        state=TrainerScheduleStates.main,
        show_mode=ShowMode.EDIT
    )


async def to_message_window(
        callback: CallbackQuery,
        widget: Button,
        dialog_manager: DialogManager
):

    default = dialog_manager.start_data['radio_default']
    dialog_manager.dialog_data['send_all'] = default

    radio: ManagedRadio = dialog_manager.find('radio')
    await radio.set_checked(default)

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

    group = get_group(dialog_manager)
    for client in group:
        if client['workouts'] or send_all:
            print(client)


async def process_selection(
        callback: CallbackQuery,
        widget: ManagedRadio,
        dialog_manager: DialogManager,
        item_id: str
):

    default = dialog_manager.start_data['radio_default']
    dialog_manager.dialog_data['send_all'] = (item_id == default)
