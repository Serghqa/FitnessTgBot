from operator import itemgetter

from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import (
    SwitchTo,
    Cancel,
    Button,
    Radio,
    Column,
    Row
)

from states import TrainerScheduleStates
from .handlers import (
    CustomCalendar,
    CustomMultiselect,
    on_date_selected,
    set_radio_default,
    apply_work,
    reset_checked,
    process_selection,
    set_checked
)
from .getters import selection_getter, get_multiselect_data, get_data_radio


RADIO = Radio(
    Format(
        text='🔘 ✅ {item[0]}'
    ),
    Format(
        text='⚪️ {item[0]}'
    ),
    id='radio_work',
    item_id_getter=itemgetter(1),
    items='radio',
    on_click=process_selection,
)


trainer_schedule_dialog = Dialog(
    Window(
        Const(
            text='Главное окно расписания'
        ),
        SwitchTo(
            Const('Редактор смены'),
            id='to_work',
            on_click=set_radio_default,
            state=TrainerScheduleStates.work,
        ),
        SwitchTo(
            Const('Создать расписание'),
            id='to_cal',
            on_click=set_radio_default,
            state=TrainerScheduleStates.schedule
        ),
        Cancel(
            text=Const('Назад'),
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
        RADIO,
        SwitchTo(
            text=Const('Назад'),
            id='cal_back',
            state=TrainerScheduleStates.main,
        ),
        getter=selection_getter,
        state=TrainerScheduleStates.schedule,
    ),
    Window(
        Const(
            text='Рабочая смена',
        ),
        Column(
            RADIO,
            id='col',
        ),
        Row(
            SwitchTo(
                text=Const('Назад'),
                id='work_back',
                state=TrainerScheduleStates.main,
            ),
            SwitchTo(
                text=Const('Редактировать'),
                id='ed_work',
                on_click=set_checked,
                state=TrainerScheduleStates.edit_work,
            ),
        ),
        getter=get_data_radio,
        state=TrainerScheduleStates.work,
    ),
    Window(
        Const(
            text='Редактор смены',
        ),
        CustomMultiselect(
            Format('{item[2]} {item[0]}'),
            Format('{item[0]}'),
            id='sel',
            item_id_getter=itemgetter(1),
            items='rows',
            min_selected=1,
        ),
        Row(
            SwitchTo(
                text=Const('Назад'),
                id='back_w',
                on_click=reset_checked,
                state=TrainerScheduleStates.work,
            ),
            Button(
                text=Const('Применить'),
                id='apply',
                on_click=apply_work,
            ),
        ),
        getter=get_multiselect_data,
        state=TrainerScheduleStates.edit_work,
    ),
)
