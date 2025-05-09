from aiogram_dialog import Dialog, Window, ShowMode
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row, Cancel, SwitchTo
from aiogram_dialog.widgets.input import TextInput

from states import ClientEditState
from .handlers import (
    workout_add,
    workout_apply,
    workout_sub,
    is_valid_type,
    successful_code,
    error_code
)
from .getters import get_data


NAME = 'name'
WORKOUTS = 'workouts'
WORKOUT = 'workout'


client_edit_dialog = Dialog(
    Window(
        Format(
            text='Окно клиента {NAME}\nТренировок {WORKOUTS}',
        ),
        SwitchTo(
            text=Const('Тренировки'),
            id='to_ed_wor',
            state=ClientEditState.workout_edit,
        ),
        Cancel(
            text=Const('В группу'),
            id='can_ed',
            show_mode=ShowMode.EDIT,
        ),
        state=ClientEditState.main,
    ),
    Window(
        Format(
            text='Тренировок {WORKOUTS}\nИзменить на {WORKOUT}',
        ),
        Row(
            Button(
                text=Const('-'),
                id='add',
                on_click=workout_sub,
            ),
            Button(
                text=Const('Применить'),
                id='apply',
                on_click=workout_apply,
            ),
            Button(
                text=Const('+'),
                id='sub',
                on_click=workout_add,
            ),
            id='row_sc',
        ),
        TextInput(
            id='ed_input',
            type_factory=is_valid_type,
            on_success=successful_code,
            on_error=error_code,
        ),
        SwitchTo(
            text=Const('Назад'),
            id='to_main',
            state=ClientEditState.main,
        ),
        state=ClientEditState.workout_edit,
    ),
    getter=get_data,
)
