from operator import itemgetter

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.kbd import (
    Button,
    Select,
    Group,
    Row,
    Radio,
    SwitchTo
)
from aiogram_dialog.widgets.input import MessageInput
from aiogram.enums import ContentType

from states import TrainerState
from .handlers import (
    set_frame,
    to_main_window,
    on_client,
    set_radio_message,
    send_message,
    next_page,
    back_page,
    get_client,
    to_schedule_dialog,
    render_group,
    process_result
)
from .getters import get_data, get_data_group, message_data


MAIN_MENU = SwitchTo(
    text=Const('Назад'),
    id='to_main',
    on_click=to_main_window,
    state=TrainerState.main,
)


trainer_dialog = Dialog(
    #  Главное окно тренера
    Window(
        Const(
            text='Главное окно тренера',
        ),
        SwitchTo(
            text=Const('Моя группа'),
            id='my_gr',
            on_click=set_frame,
            state=TrainerState.group,
        ),
        SwitchTo(
            text=Const('Сделать объявление'),
            id='send_mess',
            on_click=set_radio_message,
            state=TrainerState.message,
        ),
        Button(
            text=Const('Рассписание'),
            id='to_sched',
            on_click=to_schedule_dialog,
        ),
        getter=get_data,
        state=TrainerState.main,
    ),
    #  Окно отправки объявления
    Window(
        Const(
            text='Отправить файл или текст',
        ),
        Radio(
            Format(
                text='☑️ {item[0]}'
            ),
            Format(
                text='⬜ {item[0]}'
            ),
            id='radio_mess',
            item_id_getter=itemgetter(1),
            items='radio',
        ),
        MessageInput(
            func=send_message,
            content_types=ContentType.ANY,
        ),
        MAIN_MENU,
        getter=message_data,
        state=TrainerState.message,
    ),
    #  Окно группы
    Window(
        Const(
            text='Окно группы',
        ),
        Group(
            Group(
                Select(
                    text=Format('{item[0]}'),
                    id='cl_sel',
                    item_id_getter=itemgetter(1),
                    items='group',
                    on_click=on_client,
                ),
                id='cl_gr',
                width=1,
            ),
            Row(
                Button(
                    text=Const('⬅️'),
                    id='back',
                    on_click=back_page,
                ),
                Radio(
                    Format(
                        text='☑️ {item[0]}'
                    ),
                    Format(
                        text='⬜ {item[0]}'
                    ),
                    id='radio_pag',
                    item_id_getter=itemgetter(1),
                    items='radio',
                    on_state_changed=render_group,
                ),
                Button(
                    text=Const('➡️'),
                    id='next',
                    on_click=next_page,
                ),
                id='scr_gr',
            ),
        ),
        MessageInput(
            func=get_client,
            content_types=ContentType.ANY,
        ),
        MAIN_MENU,
        getter=get_data_group,
        state=TrainerState.group,
    ),
    on_process_result=process_result,
)
