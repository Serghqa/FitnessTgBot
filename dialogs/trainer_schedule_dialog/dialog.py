from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.text import Const
from aiogram_dialog.widgets.kbd import SwitchTo, Cancel, Row, Button

from states import TrainerScheduleStates
from .handlers import CustomCalendar, on_date_selected
from .getters import selection_getter


MAIN_MENU = SwitchTo(
    text=Const('К расписанию'),
    id='to_main',
    state=TrainerScheduleStates.main,
)


trainer_schedule_dialog = Dialog(
    Window(
        Const(
            text='Главное окно расписания'
        ),
        SwitchTo(
            Const('Выбрать смену'),
            id='to_chan',
            state=TrainerScheduleStates.work,
        ),
        SwitchTo(
            Const('Создать расписание'),
            id='to_cal',
            state=TrainerScheduleStates.schedule
        ),
        Cancel(
            text=Const('На главную'),
            id='can_sched',
            show_mode=ShowMode.EDIT,
        ),
        state=TrainerScheduleStates.main,
    ),
    Window(
        Const(
            text='Календарь'
        ),
        CustomCalendar(
            id='cal',
            on_click=on_date_selected,
        ),
        MAIN_MENU,
        getter=selection_getter,
        state=TrainerScheduleStates.schedule,
    ),
    Window(
        Const(
            text='Рабочая смена',
        ),
        Row(
            Button(
                text=Const('Смена 1 '),
                id='w1',
            ),
            Button(
                text=Const('Смена 2 '),
                id='w2',
            ),
            Button(
                text=Const('Смена 3 '),
                id='w3',
            ),
        ),
        MAIN_MENU,
        state=TrainerScheduleStates.work,
    ),
)
