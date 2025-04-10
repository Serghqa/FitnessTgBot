import logging

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row
from states import ClientEditState
from .handlers import done, workout_edit, workout_add, workout_apply
from .getters import get_data, get_workout

to_back_dialog_group = Button(
    text=Const('В группу'),
    id='to_back_dialog_group',
    on_click=done,
)


client_edit_dialog = Dialog(
    Window(
        Format(
            text='Окно клиента {name}\nТренеровок {workouts}',
        ),
        Button(
            text=Const('Тренеровки'),
            id='edit_workout',
            on_click=workout_edit,
        ),
        to_back_dialog_group,
        getter=get_data,
        state=ClientEditState.main,
    ),
    Window(
        Format(
            text='Тренеровок {workouts}\nИзменить на {workout}',
        ),
        Row(
            Button(
                text=Const('-'),
                id='add',
                on_click=workout_add,
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
            id='workout_row',
        ),
        getter=get_workout,
        state=ClientEditState.workout_edit,
    ),
)
