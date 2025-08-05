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

CLIENT = 'client'
TRAINER = 'trainer'
ID = 'id'


@start_router.message(F.text, CommandStart())
async def command_start(
        message: Message,
        dialog_manager: DialogManager,
):

    data = {TRAINER: False, CLIENT: False}

    user_data = await get_data_user(dialog_manager, Client)
    data[CLIENT] = user_data.get(ID) is not None
    if not data[CLIENT]:
        user_data = await get_data_user(dialog_manager, Trainer)
        data[TRAINER] = user_data.get(TRAINER) is not None

    data.update(user_data)

    await dialog_manager.start(
        data=data,
        state=StartSG.main,
        mode=StartMode.RESET_STACK
    )
