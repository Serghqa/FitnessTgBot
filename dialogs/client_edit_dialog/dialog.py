from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const, Format
from aiogram_dialog.widgets.kbd import Button, Row, Back
from states import ClientEditState
from .handlers import done, workout_edit, workout_add, workout_apply, workout_sub
from .getters import get_data


to_back_dialog_group = Button(
    text=Const('В группу'),
    id='to_back_dialog_group',
    on_click=done,
)


client_edit_dialog = Dialog(
    Window(
        Format(
            text='Окно клиента {name}\nТренировок {workouts}',
        ),
        Button(
            text=Const('Тренировки'),
            id='edit_workout',
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
            id='workout_row',
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
