import logging
import asyncio

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button, SwitchTo
from aiogram_dialog.widgets.input import ManagedTextInput

from db import update_workouts, get_workouts, Workout


logger = logging.getLogger(__name__)


WORKOUT = 'workout'
WORKOUTS = 'workouts'
ID = 'id'


async def workout_add(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await update_data_user(callback, widget, dialog_manager)

    dialog_manager.start_data[WORKOUT] += 1


async def workout_sub(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await update_data_user(callback, widget, dialog_manager)

    workouts = dialog_manager.start_data[WORKOUTS]

    if workouts + (dialog_manager.start_data[WORKOUT] - 1) > -1:
        dialog_manager.start_data[WORKOUT] -= 1


async def workout_apply(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await update_workouts(dialog_manager, callback)


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
        dialog_manager.start_data[WORKOUT] -= int(text[1:])

    else:
        dialog_manager.start_data[WORKOUT] += int(text)


async def error_code(
        message: Message,
        widget: ManagedTextInput,
        dialog_manager: DialogManager,
        error: ValueError
):

    await message.answer(text='Error code')


async def back_group(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await update_data_user(callback, widget, dialog_manager)
    await dialog_manager.done(
        show_mode=ShowMode.EDIT,
    )


async def update_data_user(
    callback: CallbackQuery,
    widget: SwitchTo | Button,
    dialog_manager: DialogManager
):

    data_user: dict = dialog_manager.start_data

    workout: Workout = await get_workouts(
        dialog_manager,
        dialog_manager.event.from_user.id,
        data_user[ID]
    )

    if workout.workouts != data_user[WORKOUTS]:
        await callback.answer(
            text='Данные клиента были обновленны',
            show_alert=True
        )
        data_user[WORKOUTS] = workout.workouts
