from operator import itemgetter

from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import (
    SwitchTo,
    Cancel,
    Row,
    Button,
    Multiselect
)

from states import TrainerScheduleStates
from .handlers import (
    CustomCalendar,
    on_date_selected,
    on_work,
    on_hour_selected
)
from .getters import selection_getter, get_multiselect_data


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
                on_click=on_work,
            ),
            Button(
                text=Const('Смена 2 '),
                id='w2',
                on_click=on_work,
            ),
            Button(
                text=Const('Смена 3 '),
                id='w3',
                on_click=on_work,
            ),
        ),
        MAIN_MENU,
        state=TrainerScheduleStates.work,
    ),
    Window(
        Const(
            text='Создайте смену',
        ),
        Multiselect(
            Format('✅ {item[0]}'),
            Format('{item[0]}'),
            id='m1',
            item_id_getter=itemgetter(1),
            items='rows1',
            on_click=on_hour_selected,
        ),
        Multiselect(
            Format('✅ {item[0]}'),
            Format('{item[0]}'),
            id='m2',
            item_id_getter=itemgetter(1),
            items='rows2',
            on_click=on_hour_selected,
        ),
        Multiselect(
            Format('✅ {item[0]}'),
            Format('{item[0]}'),
            id='m3',
            item_id_getter=itemgetter(1),
            items='rows3',
            on_click=on_hour_selected,
        ),
        Multiselect(
            Format('✅ {item[0]}'),
            Format('{item[0]}'),
            id='m4',
            item_id_getter=itemgetter(1),
            items='rows4',
            on_click=on_hour_selected,
        ),
        getter=get_multiselect_data,
        state=TrainerScheduleStates.start_work,
    ),
)
