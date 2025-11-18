from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import Button, Column, Row, Radio, SwitchTo
from aiogram_dialog.widgets.input import TextInput
from aiogram_dialog.widgets.text import Const, Format
from operator import itemgetter

from states import StartSG
from .getters import get_data, get_radio_data, get_timezones
from .handlers import (
    apply_tz,
    client_is_valid,
    error_code,
    is_trainer,
    is_client,
    on_trainer,
    to_client_dialog,
    to_trainer_dialog,
    trainer_is_valid,
)


CLIENT = 'is_client'
TRAINER = 'is_trainer'


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
            when=F[TRAINER] & ~F[CLIENT],
        ),
        Const(
            text='Привет клиент',
            when=F[CLIENT] & ~F[TRAINER],
        ),
        Const(
            text='Привет',
            when=F[TRAINER] & F[CLIENT],
        ),
        Row(
            SwitchTo(
                text=Const('Тренер'),
                id='tr',
                state=StartSG.trainer,
                when=~F[TRAINER],
            ),
            SwitchTo(
                text=Const('Клиент'),
                id='cl',
                state=StartSG.client,
                when=~F[CLIENT],
            ),
        ),
        Button(
            text=Const('В тренерскую'),
            id='to_tr_dlg',
            on_click=to_trainer_dialog,
            when=TRAINER,
        ),
        Button(
            text=Const('Выберите группу'),
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
            text='Введите номер вашей группы:',
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
    Window(
        Const(
            text='Ваши группы',
        ),
        Radio(
            Format(
                text='☑️ {item[0]}',
            ),
            Format(
                text='⬜ {item[0]}',
            ),
            id='radio_group',
            item_id_getter=itemgetter(1),
            items='radio',
        ),
        Button(
            Const(
                text='Перейти в выбранную группу',
            ),
            id='to_cl_dialog',
            on_click=on_trainer,
            when='is_checked',
        ),
        MAIN_MENU,
        state=StartSG.group,
        getter=get_radio_data,
    ),
    Window(
        Const(
            text='Укажите ваш часовой пояс, пожалуйста',
        ),
        Column(
            Radio(
                Format(
                    text='☑️ {item[0]}',
                ),
                Format(
                    text='⬜ {item[0]}',
                ),
                id='radio_tz',
                item_id_getter=itemgetter(1),
                items='radio_tz',
            ),
        ),
        Button(
            Const(
                text='Подтвердить',
                when='is_checked',
            ),
            id='is_tz',
            on_click=apply_tz,
        ),
        MAIN_MENU,
        state=StartSG.set_tz,
        getter=get_timezones,
    ),
)
