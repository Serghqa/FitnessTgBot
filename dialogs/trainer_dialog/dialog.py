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
    next_page,
    back_page,
    get_client,
    to_schedule
)
from .getters import get_data, get_data_group, message_data


to_main_window = Button(
    text=Const('На главную'),
    id='to_main',
    on_click=to_main_trainer_window,
)


trainer_dialog = Dialog(
    #  Главное окно тренера
    Window(
        Format(
            text='Главное окно тренера {id}',
        ),
        Button(
            text=Const('Моя группа'),
            id='my_gr',
            on_click=to_group_window,
        ),
        Button(
            text=Const('Сделать объявление'),
            id='send_mes',
            on_click=to_message_window,
        ),
        Button(
            text=Const('Рассписание'),
            id='to_sched',
            on_click=to_schedule,
        ),
        getter=get_data,
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
            id='radio',
            item_id_getter=itemgetter(1),
            items='radio',
            on_click=process_selection,
        ),
        MessageInput(
            func=send_message,
            content_types=ContentType.ANY,
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
                    id='cl_sel',
                    item_id_getter=itemgetter(1),
                    items='group',
                    on_click=on_client,
                ),
                id='cl_gr',
                width=1,
            ),
            Row(
                Button(
                    text=Const('Назад'),
                    id='back',
                    on_click=back_page,
                ),
                Button(
                    text=Const('Вперед'),
                    id='next',
                    on_click=next_page,
                ),
                id='scr_gr',
            ),
        ),
        MessageInput(
            func=get_client,
            content_types=ContentType.ANY,
        ),
        to_main_window,
        getter=get_data_group,
        state=TrainerState.group,
    ),
)
