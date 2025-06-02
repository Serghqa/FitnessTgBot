from aiogram import F

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import Button, Row, SwitchTo
from aiogram_dialog.widgets.input import TextInput

from states import StartSG
from .handlers import (
    to_trainer_dialog,
    to_client_dialog,
    is_trainer,
    is_client,
    trainer_is_valid,
    error_code,
    client_is_valid
)
from .getters import get_data


CLIENT = 'client'
TRAINER = 'trainer'


MAIN_MENU = SwitchTo(
    text=Const('Отмена'),
    id='to_main',
    state=StartSG.main,
)


validate_dialog = Dialog(
    Window(
        Const(
            text='Главное окно валидации',
        ),
        Const(
            text='Привет, выбери статус:',
            when=~F[TRAINER] & ~F[CLIENT],
        ),
        Const(
            text='Привет тренер',
            when=TRAINER,
        ),
        Const(
            text='Привет клиент',
            when=CLIENT,
        ),
        Row(
            SwitchTo(
                text=Const('Тренер'),
                id='tr',
                state=StartSG.trainer,
            ),
            SwitchTo(
                text=Const('Клиент'),
                id='cl',
                state=StartSG.client,
            ),
            #when=~F[TRAINER] & ~F[CLIENT],
        ),
        Button(
            text=Const('В тренерскую'),
            id='to_tr_dlg',
            on_click=to_trainer_dialog,
            when=TRAINER,
        ),
        Button(
            text=Const('В группу'),
            id='to_cl_dlg',
            on_click=to_client_dialog,
            when=CLIENT,
        ),
        getter=get_data,
        state=StartSG.main,
    ),
    Window(
        Const(
            text='Подтвердите, ваш статус тренера, введите код:',
        ),
        MAIN_MENU,
        TextInput(
            id='tr_valid',
            type_factory=is_trainer,
            on_success=trainer_is_valid,
            on_error=error_code,
        ),
        state=StartSG.trainer,
    ),
    Window(
        Const(
            text='Введите номер вашей группы:'
        ),
        MAIN_MENU,
        TextInput(
            id='gr_valid',
            type_factory=is_client,
            on_success=client_is_valid,
            on_error=error_code,
        ),
        state=StartSG.client,
    ),
)
