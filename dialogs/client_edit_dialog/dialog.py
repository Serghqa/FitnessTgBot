from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row, Back
from aiogram_dialog.widgets.input import TextInput

from states import ClientEditState
from .handlers import (
    done,
    workout_edit,
    workout_add,
    workout_apply,
    workout_sub,
    is_valid_type,
    successful_code,
    error_code
)
from .getters import get_data


to_back_dialog_group = Button(
    text=Const('В группу'),
    id='to_dlg_gr',
    on_click=done,
)


client_edit_dialog = Dialog(
    Window(
        Format(
            text='Окно клиента {name}\nТренировок {workouts}',
        ),
        Button(
            text=Const('Тренировки'),
            id='ed_workout',
            on_click=workout_edit,
        ),
        to_back_dialog_group,
        state=ClientEditState.main,
    ),
    Window(
        Format(
            text='Тренировок {workouts}\nИзменить на {workout}',
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
            id='row',
        ),
        TextInput(
            id='ed_input',
            type_factory=is_valid_type,
            on_success=successful_code,
            on_error=error_code,
        ),
        Row(
            Back(
                text=Const('Назад'),
                id='back',
            ),
            to_back_dialog_group,
            id='back_row',
        ),
        state=ClientEditState.workout_edit,
    ),
    getter=get_data,
)
