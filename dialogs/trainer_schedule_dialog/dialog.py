from operator import itemgetter

from aiogram import F

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import (
    Multiselect,
    SwitchTo,
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
    set_radio_work,
    set_radio_calendar,
    reset_checked,
    process_selection,
    apply_selected,
    apply_work,
    set_checked,
    reset_calendar,
    process_result,
    process_start,
    clear_selected_date,
    cancel_training,
    cancel_work
)
from .getters import (
    selection_getter,
    get_multiselect_data,
    get_data_radio,
    get_current_schedule
)


IS_CANCEL = 'is_cancel'
IS_APPLY = 'is_apply'


RADIO = Radio(
    Format(
        text='☑️ {item[0]} {item[2]}',
    ),
    Format(
        text='⬜ {item[0]} {item[2]}',
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
            on_click=set_radio_work,
            state=TrainerScheduleStates.work,
        ),
        SwitchTo(
            Const('Редактор расписания'),
            id='to_cal',
            on_click=set_radio_calendar,
            state=TrainerScheduleStates.schedule
        ),
        Button(
            text=Const('Назад'),
            id='can_sched',
            on_click=process_result,
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
        Row(
            SwitchTo(
                text=Const('Назад'),
                id='cal_back',
                on_click=reset_calendar,
                state=TrainerScheduleStates.main,
            ),
            Button(
                text=Const('Применить'),
                id='apply_cal',
                on_click=apply_selected,
                when=F[IS_APPLY],
            ),
        ),
        getter=selection_getter,
        state=TrainerScheduleStates.schedule,
    ),
    Window(
        Format(
            text='Выбранная дата {selected_date}'
        ),
        Column(
            Multiselect(
                Format('❌ {item[1]} - {item[2]}:00'),
                Format('{item[1]} - {item[2]}: 00'),
                id='sel_d',
                item_id_getter=itemgetter(0),
                items='rows',
            ),
        ),
        Row(
            SwitchTo(
                text=Const('Назад'),
                id='canc_sel',
                on_click=clear_selected_date,
                state=TrainerScheduleStates.schedule,
            ),
            Button(
                text=Const('❗Отменить запись(и)'),
                id='canc_tr',
                on_click=cancel_training,
                when=F[IS_CANCEL],
            ),
        ),
        SwitchTo(
            text=Const('‼️Отменить рабочий день'),
            id='can_work',
            state=TrainerScheduleStates.confirmation,
        ),
        getter=get_current_schedule,
        state=TrainerScheduleStates.selected_date,
    ),
    Window(
        Const(
            text='Вы действительно хотите отменить рабочий день? '\
                'Все клиенты у, которых есть запись, будут отменены.',
        ),
        SwitchTo(
            Const('Да, отменить'),
            id='can_y',
            on_click=cancel_work,
            state=TrainerScheduleStates.schedule,
        ),
        SwitchTo(
            Const('Нет, работаем'),
            id='can_n',
            state=TrainerScheduleStates.selected_date,
        ),
        state=TrainerScheduleStates.confirmation,
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
            SwitchTo(
                text=Const('Применить'),
                id='apply',
                on_click=apply_work,
                state=TrainerScheduleStates.work,
            ),
        ),
        getter=get_multiselect_data,
        state=TrainerScheduleStates.edit_work,
    ),
    on_start=process_start,
)
