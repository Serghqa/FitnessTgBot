import logging

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ShowMode
from aiogram_dialog.widgets.kbd import Button
from sqlalchemy.orm import Session
from db import update_data_client
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

    client_id = dialog_manager.start_data['id']
    value = dialog_manager.start_data['workout'] + dialog_manager.start_data['workouts']
    session: Session = dialog_manager.middleware_data['session']

    dialog_manager.start_data['workouts'] = value
    dialog_manager.start_data['workout'] = 0
    update_data_client(session, client_id, value) 
