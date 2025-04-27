import logging

from aiogram_dialog import DialogManager


logger = logging.getLogger(__name__)


async def get_data(dialog_manager: DialogManager, **kwargs):

    return dialog_manager.start_data


async def get_data_group(dialog_manager: DialogManager, **kwargs):

    group = [
        (
            f'🙋🏼‍♂️{client['name']} 🏋🏼‍♂️{client['workouts']}',
            i
        )
        for i, client in enumerate(dialog_manager.dialog_data.get('group'))
    ]

    return {'group': group}


async def message_data(dialog_manager: DialogManager, **kwargs):

    return {'radio': [('Всем', 1), ('Оплаченным', 2)]}
