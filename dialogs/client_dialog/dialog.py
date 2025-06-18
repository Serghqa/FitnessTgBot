import logging

from operator import itemgetter

from aiogram import F

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import SwitchTo, Column, Row, Multiselect, Button
from aiogram_dialog.widgets.input import TextInput

from .getters import get_data_radio, get_exist_data, get_data_selected

from .handlers import (
    send_message,
    set_calendar,
    on_date_selected,
    clear_data,
    exist_sign,
    set_client_trainings,
    on_date,
    cancel_training,
    reset_widget,
    CustomCalendar,
    CustomRadio
)

from states import ClientState


logger = logging.getLogger(__name__)

EXIST = 'exist'
WORKOUTS = 'workouts'
RADIO_ITEM = 'radio_item'


client_dialog = Dialog(
    Window(
        Const(
            text='Главное окно клиента',
        ),
        SwitchTo(
            text=Const('Написать тренеру'),
            id='mess_tr',
            state=ClientState.message,
        ),
        SwitchTo(
            text=Const('Тренировки'),
            id='sign',
            on_click=set_calendar,
            state=ClientState.schedule,
        ),
        state=ClientState.main,
    ),
    Window(
        Const(
            text='Сообщение будет отправленно вашему тренеру',
        ),
        TextInput(
            id='send_mess',
            on_success=send_message,
        ),
        state=ClientState.message,
    ),
    Window(
        Const(
            text='Расписание тренера',
        ),
        CustomCalendar(
            id='cal',
            on_click=on_date_selected,
        ),
        Row(
            SwitchTo(
                text=Const('Назад'),
                id='back_main',
                on_click=clear_data,
                state=ClientState.main,
            ),
            SwitchTo(
                text=Const('Мои записи'),
                id='my_sign',
                on_click=set_client_trainings,
                state=ClientState.my_sign_up,
            ),
        ),
        state=ClientState.schedule,
    ),
    Window(
        Const(
            text='Свободное время',
        ),
        Format(
            text='У вас есть {workouts} тренировок',
        ),
        CustomRadio(
            Format(
                text='☑️ {item[0]}:00',
            ),
            Format(
                text='⬜ {item[0]}:00',
            ),
            id='rad_sched',
            items='radio',
            item_id_getter=itemgetter(1),
        ),
        Row(
            SwitchTo(
                text=Const('Назад'),
                id='back_cal',
                on_click=set_calendar,
                state=ClientState.schedule,
            ),
            SwitchTo(
                text=Const('Записаться'),
                id='sign',
                state=ClientState.sign_up,
                on_click=exist_sign,
                when=F[WORKOUTS],
            ),
        ),
        state=ClientState.sign_training,
        getter=get_data_radio,
    ),
    Window(
        Format(
            text='Вы записаны {selected_date} в {selected_time}:00',
            when=F[EXIST]
        ),
        Format(
            text='Это время уже недоступно',
            when=~F[EXIST]
        ),
        SwitchTo(
            text=Const('Назад'),
            id='back_exist',
            state=ClientState.sign_training,
            on_click=set_calendar,
        ),
        state=ClientState.sign_up,
        getter=get_exist_data,
    ),
    Window(
        Const(
            text='Мои записи на тренировку',
        ),
        CustomCalendar(
            id='my_train',
            on_click=on_date,
        ),
        SwitchTo(
            text=Const('Назад'),
            id='can_my_tr',
            state=ClientState.schedule,
            on_click=set_calendar,
        ),
        state=ClientState.my_sign_up,
    ),
    Window(
        Format(
            text='Выбранная дата {selected_date}'
        ),
        Column(
            Multiselect(
                Format('❌ {item[1]}:00'),
                Format('{item[1]}: 00'),
                id='sel_d',
                item_id_getter=itemgetter(0),
                items='rows',
            ),
        ),
        Row(
            SwitchTo(
                text=Const('Назад'),
                id='canc_sel',
                on_click=reset_widget,
                state=ClientState.my_sign_up,
            ),
            Button(
                text=Const('❗Отменить запись(и)'),
                id='canc_tr',
                on_click=cancel_training,
                when=F[EXIST]
            ),
        ),
        getter=get_data_selected,
        state=ClientState.cancel_training,
    ),
)
