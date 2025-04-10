import logging

from operator import itemgetter
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.kbd import Button, Select, Group, Row, Radio
from aiogram_dialog.widgets.input import MessageInput
from aiogram.enums import ContentType
from states import TrainerState
from .handlers import (
    to_group_window,
    to_main_trainer_window,
    on_client,
    to_message_window,
    send_message,
    process_selection,
    set_radio_default,
    process_result
)
from .getters import get_data_group, message_data


logger = logging.getLogger(__name__)

to_main_window = Button(
    text=Const('На главную'),
    id='to_main',
    on_click=to_main_trainer_window,
)


trainer_dialog = Dialog(
    #  Главное окно тренера
    Window(
        Format(
            text='Главное окно тренера',
        ),
        Button(
            text=Const('Моя группа'),
            id='my_group',
            on_click=to_group_window,
        ),
        Button(
            text=Const('Сделать объявление'),
            id='send_message',
            on_click=to_message_window,
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
            on_click=process_selection,
        ),
        MessageInput(
            func=send_message,
            content_types=ContentType.ANY,
            filter=lambda x: True,
        ),
        to_main_window,
        getter=message_data,
        state=TrainerState.message,
    ),
    #  Окно группы
    Window(
        Format(
            text='Окно группы',
        ),
        Group(
            Group(
                Select(
                  text=Format('{item[0]}'),
                  id='client_select',
                  item_id_getter=itemgetter(1),
                  items='group',
                  on_click=on_client,
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
                id='scroll_group',
            ),
        ),
        to_main_window,
        getter=get_data_group,
        state=TrainerState.group,
    ),
    on_start=set_radio_default,
    on_process_result=process_result,
)
