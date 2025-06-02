import logging

from aiogram.enums import ContentType

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import SwitchTo
from aiogram_dialog.widgets.input import TextInput

from .handlers import send_message, set_calendar, on_date_selected, CustomCalendar

from states import ClientState


logger = logging.getLogger(__name__)


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
        state=ClientState.schedule,
    ),
)
