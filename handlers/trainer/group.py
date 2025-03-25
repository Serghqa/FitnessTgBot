import logging

from pprint import pprint
from aiogram.types import CallbackQuery, Update
from aiogram_dialog import DialogManager
from aiogram_dialog.widgets.kbd import Button
from tmp_db import data_base
from states.trainer_states import TrainerState


logger = logging.getLogger(__name__)


#  -----Handlers-----


async def to_main(
    callback: CallbackQuery,
    widget: Button,
    dialog_manager: DialogManager
):
    await dialog_manager.switch_to(state=TrainerState.main)


#  -----Getters-----


async def get_data_group(dialog_manager: DialogManager, **kwargs):

    frame: dict[str, int] = dialog_manager.dialog_data.get('frame')
    start, step = frame.values()
    trainer_id = str(kwargs.get('event_from_user').id)
    group: list[tuple[str]] | None = data_base['trainers'].get(trainer_id)
    update: Update = kwargs.get('event_update')
    if update.callback_query:
        if update.callback_query.data.endswith('group_next'):
            if start + step < len(group):
                start = start + step
            else:
                start = 0
        elif update.callback_query.data.endswith('group_prev'):
            if start - step >= 0:
                start = start - step
        dialog_manager.dialog_data['frame']['start'] = start
    return {'trainer_id': trainer_id, 'group': group[start:start+step]}
