import logging

from aiogram.types import CallbackQuery, Message
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.input import ManagedTextInput
from aiogram_dialog.widgets.kbd import Button, SwitchTo

from db import get_workouts, update_workouts, Workout
from schemas import ClientSchema
from notification import send_notification


logger = logging.getLogger(__name__)

ID = 'id'
WORKOUT = 'workout'
WORKOUTS = 'workouts'


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

    user_id: int = dialog_manager.start_data.get(ID)
    workouts: int = dialog_manager.start_data.get(WORKOUTS)
    text = (
        f'Количество тренировок было изменено, '
        f'теперь у вас {workouts}'
    )

    await send_notification(
        bot=dialog_manager.event.bot,
        user_id=user_id,
        text=text,
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
        workout = dialog_manager.start_data[WORKOUT] - int(text[1:])
        if (dialog_manager.start_data[WORKOUTS] + workout) < 0:
            workout = abs(
                dialog_manager.start_data[WORKOUTS] + workout
            ) + workout

    else:
        workout = dialog_manager.start_data[WORKOUT] + int(text)

    dialog_manager.start_data[WORKOUT] = workout


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
        result=dialog_manager.start_data,
        show_mode=ShowMode.EDIT,
    )


async def update_data_user(
    callback: CallbackQuery,
    widget: SwitchTo | Button,
    dialog_manager: DialogManager
):

    data_user: dict = dialog_manager.start_data
    client: ClientSchema = ClientSchema(**data_user)

    workout: Workout = await get_workouts(
        dialog_manager=dialog_manager,
        trainer_id=dialog_manager.event.from_user.id,
        client_id=client.id,
    )

    if workout.workouts != client.workouts:
        await callback.answer(
            text='Данные клиента были обновленны',
            show_alert=True,
        )
    data_user[WORKOUTS] = workout.workouts
