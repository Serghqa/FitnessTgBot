import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import ManagedTextInput
from sqlalchemy.orm import Session
from db import update_workouts_client
from states import ClientEditState


logger = logging.getLogger(__name__)


async def done(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await dialog_manager.done(show_mode=ShowMode.EDIT)


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

    dialog_manager.start_data['workout'] += 1


async def workout_sub(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    workouts = dialog_manager.start_data['workouts']

    if workouts + (dialog_manager.start_data['workout'] - 1) > -1:
        dialog_manager.start_data['workout'] -= 1


async def workout_apply(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    update_workouts_client(dialog_manager)


def is_valid_type(code: str):

    sign = ''

    if code.startswith('-'):
        sign = '-'
        code = code[1:]

    if code.isdigit() and int(code) < 100:
        return sign + code

    raise ValueError


async def successful_code(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        text: str
):

    if text.startswith('-'):
        dialog_manager.start_data['workout'] -= int(text[1:])

    else:
        dialog_manager.start_data['workout'] += int(text)


async def error_code(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError
):

    await message.answer(text='Error code')
