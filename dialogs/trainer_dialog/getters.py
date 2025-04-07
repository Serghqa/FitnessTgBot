import logging

from aiogram.types import Update
from aiogram_dialog import DialogManager


logger = logging.getLogger(__name__)


async def get_data_group(dialog_manager: DialogManager, **kwargs):

    frame: dict[str, int] = dialog_manager.dialog_data['data']['frame']
    start, step = frame.values()
    group: list[dict] = [(client['name'], client['client_id']) for client in dialog_manager.dialog_data['data']['group']]
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
        dialog_manager.dialog_data['data']['frame']['start'] = start
    return {'group': group[start:start+step]}


async def message_data(dialog_manager: DialogManager, **kwargs):
    return {'radio': [('Всем', 1), ('Оплаченным', 2)]}
