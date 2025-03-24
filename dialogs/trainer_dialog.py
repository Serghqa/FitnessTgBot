import logging
import handlers

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.kbd import Button
from states import TrainerState

logger = logging.getLogger(__name__)

tariner_dialog = Dialog(
    Window(
        Format(
            text='Главное окно тренера',
        ),
        Button(
            text=Const('Моя группа'),
            id='my_group',
            on_click=handlers.trainer.main.to_group,
        ),
        state=TrainerState.main,
    ),
    Window(
        Format(
            text='Окно группы {trainer_id}',
        ),
        Button(
            text=Const('Назад'),
            id='to_main_trainer',
            on_click=handlers.trainer.group.to_back_main,
        ),
        getter=handlers.trainer.group.get_data_group,
        state=TrainerState.group,
    ),
)
