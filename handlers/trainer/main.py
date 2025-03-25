import logging

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from states.trainer_states import TrainerState


logger = logging.getLogger(__name__)

#  ----Handlers-----


async def to_group(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):
    dialog_manager.dialog_data['frame'] = {'start': 0, 'step': 5}
    await dialog_manager.switch_to(state=TrainerState.group)
