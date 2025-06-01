import logging

from typing import Any

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode, Data
from aiogram_dialog.widgets.kbd import Button, Select, ManagedRadio, SwitchTo
from aiogram_dialog.widgets.kbd.select import ManagedRadio
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
RADIO_MESS = 'radio_mess'
RADIO_GROUP = 'radio_pag'
RADIO_WORK = 'radio_work'
SEND_ALL = 'send_all'
WORK_DEFAULT = 'work_default'
SCHEDULES = 'schedules'
WIDGET_DATA = 'widget_data'


def _get_curent_widget_context(
    dialog_manager: DialogManager,
    key: str,
    default='1'
) -> Any:

    context: Context = dialog_manager.current_context()
    widget_data = context.widget_data.get(key, default)

    return widget_data


async def get_client(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager
):

    if not message.text:
        await message.answer('Ввели не корректные данные')

    elif message.text.isdigit():
        data: dict = await get_data_user(dialog_manager, Client, int(message.text))

        if data:
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


async def _set_frame_group(
    dialog_manager: DialogManager,
    limit: int
) -> None:

    context: Context = dialog_manager.current_context()
    all: bool = context.widget_data.get(RADIO_GROUP) == '1'

    dialog_manager.dialog_data[OFFSET] += limit

    if dialog_manager.dialog_data[OFFSET] < 0:
        dialog_manager.dialog_data[OFFSET] = 0

    group: list[dict] = await get_group(dialog_manager, all)

    if not group and dialog_manager.dialog_data[OFFSET] > 0:
        dialog_manager.dialog_data[OFFSET] = 0
        group: list[dict] = await get_group(dialog_manager, all)

    dialog_manager.dialog_data[GROUP] = group


async def _set_radio_group(
    dialog_manager: DialogManager
):

    widget_item: str = _get_curent_widget_context(dialog_manager, RADIO_GROUP)

    radio: ManagedRadio = dialog_manager.find(RADIO_GROUP)
    await radio.set_checked(widget_item)


async def render_group(
    callback: CallbackQuery,
    widget: ManagedRadio,
    dialog_manager: DialogManager,
    item_id: str
):

    await widget.set_checked(item_id)
    await set_frame(callback, widget, dialog_manager)
    await dialog_manager.update(dialog_manager.dialog_data)


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

    await _set_radio_group(dialog_manager)
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


async def to_schedule_dialog(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    widget_item: str = _get_curent_widget_context(dialog_manager, RADIO_WORK)
    work_days: list[WorkingDay] = \
        await get_work_days(dialog_manager)

    work_days_data: dict[int, str] = {
        day.item: day.work for day in work_days
    }

    data = {}

    data[SCHEDULES] = {id: work for id, work in sorted(work_days_data.items())}
    data[WIDGET_DATA] = {RADIO_WORK: widget_item}

    await dialog_manager.start(
        data=data,
        state=TrainerScheduleStates.main,
        show_mode=ShowMode.EDIT
    )


async def set_radio_message(
        callback: CallbackQuery,
        widget: SwitchTo,
        dialog_manager: DialogManager
):

    widget_item: str = _get_curent_widget_context(dialog_manager, RADIO_MESS)

    radio: ManagedRadio = dialog_manager.find(RADIO_MESS)
    await radio.set_checked(widget_item)


async def send_message(
        message: Message,
        widget: MessageInput,
        dialog_manager: DialogManager
):

    widget_item: str = _get_curent_widget_context(dialog_manager, RADIO_MESS)

    dialog_manager.dialog_data.update(
        {
            OFFSET: 0,
            LIMIT: 5
        }
    )

    if widget_item == '2':
        group: list[dict] = await get_group(dialog_manager, False)

    else:
        group: list[dict] = await get_group(dialog_manager)

    for user in group:
        print(user)


async def process_result(
    start_data: Data,
    result: dict | None,
    dialog_manager: DialogManager
):
    if result:
        context: Context = dialog_manager.current_context()
        context.widget_data.update(result)
