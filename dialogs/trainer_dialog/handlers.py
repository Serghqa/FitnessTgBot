import logging

from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button, Select, ManagedRadio, SwitchTo
from aiogram_dialog.widgets.input import MessageInput
from aiogram_dialog.api.entities.context import Context

from states import TrainerState, TrainerScheduleStates, ClientEditState
from db import Client, WorkingDay, get_group, get_data_user, get_work_days


logger = logging.getLogger(__name__)


GROUP = 'group'
CLIENT = 'client'
ID = 'id'
WORKOUT = 'workout'
WORKOUTS = 'workouts'
OFFSET = 'offset'
LIMIT = 'limit'
RADIO_DEFAULT = 'radio_default'
SEND_ALL = 'send_all'
RADIO = 'radio_mess'
WORK_DEFAULT = 'work_default'
SCHEDULES = 'schedules'


async def get_client(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager
):

    if not message.text:
        await message.answer('Ввели не корректные данные')

    elif message.text.isdigit():
        data = await get_data_user(dialog_manager, Client, int(message.text))

        if data[CLIENT]:
            for user in dialog_manager.dialog_data[GROUP]:
                if data[ID] == user[ID]:
                    user[WORKOUT] = 0

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


async def _set_frame_group(dialog_manager: DialogManager, limit: int) -> None:

    dialog_manager.dialog_data[OFFSET] += limit

    if dialog_manager.dialog_data[OFFSET] < 0:
        dialog_manager.dialog_data[OFFSET] = 0

    group: list[dict] = await get_group(dialog_manager)

    if not group and dialog_manager.dialog_data[OFFSET] > 0:
        dialog_manager.dialog_data[OFFSET] = 0
        group: list[dict] = await get_group(dialog_manager)

    dialog_manager.dialog_data[GROUP] = group


async def set_frame(
    callback: CallbackQuery,
    widget: SwitchTo,
    dialog_manager: DialogManager
):

    dialog_manager.dialog_data.update(
        {
            OFFSET: 0,
            LIMIT: 5
        }
    )
    await _set_frame_group(dialog_manager, 0)


async def next_page(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await _set_frame_group(
        dialog_manager,
        dialog_manager.dialog_data[LIMIT]
    )


async def back_page(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await _set_frame_group(
        dialog_manager,
        -(dialog_manager.dialog_data[LIMIT])
    )


async def to_main_window(
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

    data: dict[str, Any] = dialog_manager.dialog_data[GROUP][int(item_id)]
    data[WORKOUT] = 0

    await dialog_manager.start(
        state=ClientEditState.main,
        data=data,
        show_mode=ShowMode.EDIT
    )


async def to_schedule_dlg(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):
    
    work_days: list[WorkingDay] = \
        await get_work_days(dialog_manager)
    
    data = {}
    work_days_data: dict[int, dict] = {day.id: day.get_data() for day in work_days}
    
    default = dialog_manager.start_data[RADIO_DEFAULT]
    
    data[WORK_DEFAULT] = default
    data[SCHEDULES] = work_days_data

    await dialog_manager.start(
        data=data,
        state=TrainerScheduleStates.main,
        show_mode=ShowMode.EDIT
    )


async def set_radio_default(
        callback: CallbackQuery,
        widget: SwitchTo,
        dialog_manager: DialogManager
):
    
    context: Context = dialog_manager.current_context()
    default = context.widget_data.get(RADIO, '1')

    radio: ManagedRadio = dialog_manager.find(RADIO)
    await radio.set_checked(default)


async def send_message(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager
):

    context: Context = dialog_manager.current_context()
    item_id = context.widget_data.get(RADIO)

    dialog_manager.dialog_data.update(
        {
            OFFSET: 0,
            LIMIT: 5
        }
    )

    if item_id == '2':
        group: list[dict] = await get_group(dialog_manager, False)

    else:
        group: list[dict] = await get_group(dialog_manager)

    for user in group:
        print(user)    
