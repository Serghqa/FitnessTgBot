import logging

from aiogram_dialog import DialogManager
from typing import Any


logger = logging.getLogger(__name__)

NAME = 'name'
WORKOUTS = 'workouts'
GROUP = 'group'
RADIO = 'radio'


async def get_data(
    dialog_manager: DialogManager,
    **kwargs
) -> dict[str, Any]:

    return dialog_manager.start_data


async def get_data_group(
    dialog_manager: DialogManager,
    **kwargs
) -> dict[str, Any]:
    """
    Функция-получатель для диалогового окна, отображающего список клиентов
    и параметров радиопереключателей.
    """

    group = [
        (
            f'🙋🏼‍♂️{client[NAME]} 🏋🏼‍♂️{client[WORKOUTS]}',
            i
        )
        for i, client in enumerate(dialog_manager.dialog_data.get(GROUP, []))
    ]

    return {GROUP: group, RADIO: [('FREE', 1), ('ᴠɪᴘ', 2)]}
