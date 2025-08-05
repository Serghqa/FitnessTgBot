import logging

from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities.context import Context

from db import Trainer


RADIO = 'radio'
RADIO_GROUP = 'radio_group'
TRAINERS = 'trainers'


logger = logging.getLogger(__name__)


async def get_data(dialog_manager: DialogManager, **kwargs):

    return dialog_manager.start_data


async def get_radio_data(dialog_manager: DialogManager, **kwargs):

    context: Context = dialog_manager.current_context()

    is_checked: str | None = context.widget_data.get(RADIO_GROUP)

    trainers: list[Trainer] = dialog_manager.dialog_data[TRAINERS]

    return {
        'is_checked': is_checked,
        RADIO: [(trainer.name, i) for i, trainer in enumerate(trainers)]
    }
