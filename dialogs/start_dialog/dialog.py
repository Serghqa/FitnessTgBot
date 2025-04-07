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
from db import add_user_db, get_client, get_trainer


logger = logging.getLogger(__name__)

start_router = Router()


@start_router.message(F.text, CommandStart())
async def command_start(
        message: Message,
        dialog_manager: DialogManager
):
    user_id = message.from_user.id
    session: Session = dialog_manager.middleware_data.get('session')
    trainer = None
    client = get_client(session, user_id)
    if not client:
        trainer = get_trainer(session, user_id)
    user = not trainer and not client
    data = {'user': user, 'trainer': trainer, 'client': client}

    await dialog_manager.start(
        data=data,
        state=StartSG.start,
        mode=StartMode.RESET_STACK
    )
