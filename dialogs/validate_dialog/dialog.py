import logging

from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.input import TextInput
from states import StartSG
from .handlers import (
    is_trainer,
    to_trainer_dialog,
    is_client,
    to_client_dialog,
    to_main_start_window,
    valid_code,
    is_valid_client,
    successful_code,
    error_code,
    successful_client_code
)
from .getters import get_data


logger = logging.getLogger(__name__)

to_main_window = Button(
    text=Const('Отмена'),
    id='to_main',
    on_click=to_main_start_window,
)


start_dialog = Dialog(
    Window(
        Format(
            text='Главное стартовое окно',
        ),
        Format(
            text='Привет, выбери статус:',
            when=~F['user'],
        ),
        Format(
            text='Привет тренер',
            when='trainer',
        ),
        Format(
            text='Привет клиент',
            when='client',
        ),
        Row(
            Button(
                text=Const('Тренер'),
                id='is_trainer',
                on_click=is_trainer,
            ),
            Button(
                text=Const('Клиент'),
                id='is_client',
                on_click=is_client,
            ),
            when=~F['user'],
        ),
        Row(
            Button(
                text=Const('В тренерскую'),
                id='to_tr_dlg',
                on_click=to_trainer_dialog,
                when='trainer',
            ),
        ),
        Row(
            Button(
                text=Const('В группу'),
                id='to_cl_dlg',
                on_click=to_client_dialog,
                when='client',
            ),
        ),
        getter=get_data,
        state=StartSG.start,
    ),
    Window(
        Format(
            text='Подтвердите, ваш статус тренера, введите код:',
        ),
        to_main_window,
        TextInput(
            id='tr_valid',
            type_factory=valid_code,
            on_success=successful_code,
            on_error=error_code,
        ),
        state=StartSG.trainer_validate,
    ),
    Window(
        Format(
            text='Введите номер вашей группы:'
        ),
        to_main_window,
        TextInput(
            id='gr_valid',
            type_factory=is_valid_client,
            on_success=successful_client_code,
            on_error=error_code,
        ),
        state=StartSG.client_validate,
    ),
)
