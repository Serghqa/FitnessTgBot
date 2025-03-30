import logging
import handlers

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram.enums import ContentType
from aiogram_dialog import (
    DialogManager,
    StartMode,
    Dialog,
    Window
)
from aiogram_dialog.widgets.text import Format, Const
from aiogram_dialog.widgets.kbd import Button, Row
from aiogram_dialog.widgets.input import TextInput
from states import StartSG


logger = logging.getLogger(__name__)

router = Router()

to_main_window = Button(
    text=Const('Отмена'),
    id='to_main',
    on_click=handlers.to_main_start_window,
)


@router.message(F.text, CommandStart())
async def command_start(
        message: Message,
        dialog_manager: DialogManager
):
    await dialog_manager.start(
        state=StartSG.start,
        mode=StartMode.RESET_STACK
    )


start_dialog = Dialog(
    Window(
        Format(
            text='Главное стартовое окно',
        ),
        Format(
            text='Привет, выбери статус:',
            when=~F['user'],
        ),
        Format(
            text='Привет тренер',
            when='trainer',
        ),
        Format(
            text='Привет клиент',
            when='client',
        ),
        Row(
            Button(
                text=Const('Тренер'),
                id='is_trainer',
                on_click=handlers.is_trainer,
            ),
            Button(
                text=Const('Клиент'),
                id='is_client',
                on_click=handlers.is_client,
            ),
            when=~F['user'],
        ),
        Row(
            Button(
                text=Const('В тренерскую'),
                id='to_tr_dlg',
                on_click=handlers.to_trainer_dialog,
                when='trainer',
            ),
        ),
        Row(
            Button(
                text=Const('В группу'),
                id='to_cl_dlg',
                on_click=handlers.to_client_dialog,
                when='client',
            ),
        ),
        getter=handlers.get_data,
        state=StartSG.start,
    ),
    Window(
        Format(
            text='Подтвердите, ваш статус тренера, введите код:',
        ),
        to_main_window,
        TextInput(
            id='tr_valid',
            type_factory=handlers.valid_code,
            on_success=handlers.successful_code,
            on_error=handlers.error_code,
        ),
        state=StartSG.trainer_validate,
    ),
    Window(
        Format(
            text='Введите номер вашей группы:'
        ),
        to_main_window,
        TextInput(
            id='gr_valid',
            type_factory=handlers.is_valid_client,
            on_success=handlers.successful_client_code,
            on_error=handlers.error_code,
        ),
        state=StartSG.client_validate,
    ),
)
