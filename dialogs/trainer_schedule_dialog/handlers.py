import logging

from datetime import date

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager, ShowMode, ChatEvent
from aiogram_dialog.widgets.kbd import Button, ManagedCalendar

from states import TrainerScheduleStates


logger = logging.getLogger(__name__)


async def done(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await dialog_manager.done(show_mode=ShowMode.EDIT)


async def to_main_schedule_window(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await dialog_manager.switch_to(state=TrainerScheduleStates.main)


async def to_create_schedule(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):

    await dialog_manager.switch_to(state=TrainerScheduleStates.create_schedule)


async def on_date_clicked(
    callback: ChatEvent,
    widget: ManagedCalendar,
    manager: DialogManager,
    selected_date: date, /,
):

    await callback.answer(str(selected_date))
