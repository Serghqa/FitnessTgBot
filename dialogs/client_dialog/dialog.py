import logging

from operator import itemgetter

from aiogram import F

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import SwitchTo, Radio, Column
from aiogram_dialog.widgets.input import TextInput

from .getters import get_data_radio, get_exist_data

from .handlers import (
    send_message,
    set_calendar,
    on_date_selected,
    process_selection,
    clear_data,
    reset_radio,
    exist_sign,
    CustomCalendar,
    CustomRadio
)

from states import ClientState


logger = logging.getLogger(__name__)

EXIST = 'exist'
WORKOUTS = 'workouts'


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
            text=Const('Записаться на тренировку'),
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
        SwitchTo(
            text=Const('Назад'),
            id='back_main',
            on_click=clear_data,
            state=ClientState.main,
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
            on_click=process_selection,
        ),
        SwitchTo(
            text=Const('Назад'),
            id='back_cal',
            on_click=reset_radio,
            state=ClientState.schedule,
        ),
        SwitchTo(
            text=Const('Записаться'),
            id='sign',
            state=ClientState.sign_up,
            on_click=exist_sign,
            when=F[WORKOUTS],
        ),
        state=ClientState.sign_training,
        getter=get_data_radio,
    ),
    Window(
        Format(
            text='Вы записаны {selected_date} в {time}:00',
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
)
