import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button
from aiogram_dialog.widgets.input import ManagedTextInput

from db import update_workouts


logger = logging.getLogger(__name__)


WORKOUT = 'workout'
WORKOUTS = 'workouts'


async def workout_add(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    dialog_manager.start_data[WORKOUT] += 1


async def workout_sub(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    workouts = dialog_manager.start_data[WORKOUTS]

    if workouts + (dialog_manager.start_data[WORKOUT] - 1) > -1:
        dialog_manager.start_data[WORKOUT] -= 1


async def workout_apply(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    try:
        await update_workouts(dialog_manager)
    except ValueError:
        await callback.answer(
            text='Во время редактирования, клиент производил операции связанные с записью,' \
                ' данные были измененны.' \
                ' Повторите вашу операцию еще раз, пожалуйста!',
            show_alert=True,
        )


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
    
    await dialog_manager.done(
        show_mode=ShowMode.EDIT,
    )
