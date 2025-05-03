import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram_dialog import (
    DialogManager,
    StartMode
)

from states import StartSG
from db import Client, Trainer, get_data_user


logger = logging.getLogger(__name__)

start_router = Router()


@start_router.message(F.text, CommandStart())
async def command_start(
        message: Message,
        dialog_manager: DialogManager,
):

    data = await get_data_user(dialog_manager, Client)
    if not data.get('client'):
        data = await get_data_user(dialog_manager, Trainer)

    await dialog_manager.start(
        data=data,
        state=StartSG.main,
        mode=StartMode.RESET_STACK
    )
