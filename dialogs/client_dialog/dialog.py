import logging

from aiogram import F
from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.kbd import (
    Button,
    Column,
    Multiselect,
    Row,
    SwitchTo,
)
from aiogram_dialog.widgets.text import Const, Format
from operator import itemgetter

from .getters import (
    get_data_radio,
    get_data_selected,
    get_data_today,
    get_exist_data,
)
from .handlers import (
    cancel_training,
    clear_data,
    CustomCalendar,
    CustomRadio,
    exist_sign,
    on_date,
    on_date_selected,
    back_trainings,
    set_calendar,
    set_trainings,
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
        Button(
            text=Const('Тренировки'),
            id='sign',
            on_click=set_calendar,
        ),
        state=ClientState.main,
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
            Button(
                text=Const('Мои записи'),
                id='my_sign',
                on_click=set_trainings,
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
            Button(
                text=Const('Назад'),
                id='back_cal',
                on_click=set_calendar,
            ),
            Button(
                text=Const('Записаться'),
                id='sign',
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
            when=F[EXIST],
        ),
        Format(
            text='Этого времени не существует или оно уже занято.',
            when=~F[EXIST],
        ),
        Button(
            text=Const('Назад'),
            id='back_exist',
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
        Button(
            text=Const('Назад'),
            id='can_my_tr',
            on_click=set_calendar,
        ),
        state=ClientState.my_sign_up,
    ),
    Window(
        Format(
            text='Выбранная дата {selected_date}',
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
            Button(
                text=Const('Назад'),
                id='canc_sel',
                on_click=back_trainings,
            ),
            Button(
                text=Const('❗Отменить запись(и)'),
                id='canc_tr',
                on_click=cancel_training,
                when=F[EXIST],
            ),
        ),
        getter=get_data_selected,
        state=ClientState.cancel_training,
    ),
    Window(
        Format(
            text='Сегодня {today}',
        ),
        Format(
            text='{text}'
        ),
        Button(
            text=Const('Назад'),
            id='back_sch',
            on_click=set_trainings,
        ),
        getter=get_data_today,
        state=ClientState.today,
    ),
)
