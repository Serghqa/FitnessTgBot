import logging

from aiogram.types import Update
from aiogram_dialog import DialogManager
from test import test_trainer_true, test_not_data


logger = logging.getLogger(__name__)


async def get_data(dialog_manager: DialogManager, **kwargs):

    test_trainer_true(dialog_manager.start_data)  # test start_data is trainer
    test_not_data(dialog_manager.dialog_data)  # test dialog_data is empty

    return dialog_manager.start_data


async def get_data_group(dialog_manager: DialogManager, **kwargs):

    FRAME: dict[str, int] = dialog_manager.dialog_data.get('frame')
    start, step = FRAME.values()
    group = [
        (
            f'🙋🏼‍♂️{client['name']} 🏋🏼‍♂️{client['workouts']}',
            i
        )
        for i, client in enumerate(dialog_manager.dialog_data['group'])
    ]
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

    return {'group': group[start:start+step]}


async def message_data(dialog_manager: DialogManager, **kwargs):

    return {'radio': [('Всем', 1), ('Оплаченным', 2)]}
