import logging
import handlers

from operator import itemgetter
from aiogram_dialog import Dialog, Window, DialogManager
from aiogram.types import CallbackQuery
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.kbd import Button, Select, Group, Row, Radio
from aiogram_dialog.widgets.input import TextInput, MessageInput
from aiogram.enums import ContentType
from states import TrainerState
from tmp_db import data_base

logger = logging.getLogger(__name__)

to_main_window = Button(
    text=Const('На главную'),
    id='to_main',
    on_click=handlers.to_main_trainer_window,
)


tariner_dialog = Dialog(
    #  Главное окно тренера
    Window(
        Format(
            text='Главное окно тренера',
        ),
        Button(
            text=Const('Моя группа'),
            id='my_group',
            on_click=handlers.to_group_window,
        ),
        Button(
            text=Const('Сделать объявление'),
            id='send_message',
            on_click=handlers.to_message_window,
        ),
        state=TrainerState.main,
    ),
    #  Окно отправки объявления
    Window(
        Format(
            text='Отправить файл или текст',
        ),
        Radio(
            Format(
                text='🔘 {item[0]}'
            ),
            Format(
                text='⚪️ {item[0]}'
            ),
            id='send_checked',
            item_id_getter=itemgetter(1),
            items='radio',
            on_click=handlers.process_selection,
        ),
        MessageInput(
            func=handlers.send_message,
            content_types=ContentType.ANY,
            filter=lambda x: True,
        ),
        to_main_window,
        getter=handlers.message_data,
        state=TrainerState.message,
    ),
    #  Окно группы
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
                  on_click=handlers.on_client,
                ),
                id='client_select',
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
                id='row_group',
            ),
        ),
        to_main_window,
        getter=handlers.trainer.get_data_group,
        state=TrainerState.group,
    ),
)
