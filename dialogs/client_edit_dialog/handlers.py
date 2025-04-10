import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, StartMode, ShowMode
from aiogram_dialog.widgets.kbd import Button, Select, ManagedRadio
from aiogram_dialog.widgets.input import MessageInput
from sqlalchemy.orm import Session
from states import ClientEditState


async def done(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await dialog_manager.done(
        result=dialog_manager.start_data,
        show_mode=ShowMode.EDIT
    )


async def workout_edit(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await dialog_manager.switch_to(
        state=ClientEditState.workout_edit,
        show_mode=ShowMode.EDIT
    )


async def workout_add(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    dialog_manager.dialog_data['workout'] += 1


async def workout_sub(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    dialog_manager.dialog_data['workout'] -= 1


async def workout_apply(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    print(widget.text)
