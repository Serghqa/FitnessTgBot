import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram_dialog import (
    DialogManager,
    StartMode
)
from sqlalchemy.orm import Session
from states import StartSG
from db import get_data_user


logger = logging.getLogger(__name__)

start_router = Router()


@start_router.message(F.text, CommandStart())
async def command_start(
        message: Message,
        dialog_manager: DialogManager
):

    session: Session = dialog_manager.middleware_data.get('session')

    user_data = get_data_user(session, dialog_manager)

    await dialog_manager.start(
        data=user_data,
        state=StartSG.start,
        mode=StartMode.RESET_STACK
    )
