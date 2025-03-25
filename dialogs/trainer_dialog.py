import logging
import handlers

from operator import itemgetter
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.kbd import Button, Select, Group, Row
from states import TrainerState
from tmp_db import data_base

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
        Group(
            Group(
                Select(
                  text=Format('{item[0]}'),
                  id='client_select',
                  item_id_getter=itemgetter(1),
                  items='group',
                ),
                id='client_group',
                width=1,
            ),
            Row(
                Button(
                    text=Const('Назад'),
                    id='group_prev',
                ),
                Button(
                    text=Const('Вперед'),
                    id='group_next',
                ),
                id='row',
            ),
        ),
        Button(
            text=Const('На главную'),
            id='to_main',
            on_click=handlers.trainer.group.to_main,
        ),
        getter=handlers.trainer.group.get_data_group,
        state=TrainerState.group,
    ),
)
