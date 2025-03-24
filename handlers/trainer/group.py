import logging

from aiogram.types import CallbackQuery
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from tmp_db import data_base
from states.trainer_states import TrainerState


logger = logging.getLogger(__name__)


#  -----Handlers-----


async def to_back_main(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):
    await dialog_manager.switch_to(state=TrainerState.main)


#  -----Getters-----


async def get_data_group(**kwargs):
    trainer_id = kwargs['event_from_user'].id
    group = data_base['trainers'].get(trainer_id)
    return {'trainer_id': trainer_id, 'group': group}
