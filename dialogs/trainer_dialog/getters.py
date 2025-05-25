import logging

from aiogram_dialog import DialogManager


logger = logging.getLogger(__name__)


NAME = 'name'
WORKOUTS = 'workouts'
GROUP = 'group'
RADIO = 'radio'


async def get_data(dialog_manager: DialogManager, **kwargs):

    return dialog_manager.start_data


async def get_data_group(dialog_manager: DialogManager, **kwargs):

    group = [
        (
            f'🙋🏼‍♂️{client[NAME]} 🏋🏼‍♂️{client[WORKOUTS]}',
            i
        )
        for i, client in enumerate(dialog_manager.dialog_data.get(GROUP))
    ]

    return {GROUP: group, RADIO: [('FREE', 1), ('ᴠɪᴘ', 2)]}


async def message_data(dialog_manager: DialogManager, **kwargs):

    return {RADIO: [('Всем', 1), ('Активные', 2)]}
