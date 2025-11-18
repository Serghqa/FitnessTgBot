import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import (
    DialogManager,
    StartMode,
)
from sqlalchemy.ext.asyncio import AsyncSession

from db import Client, get_user, Trainer
from schemas import ClientSchema, TrainerSchema
from states import StartSG

logger = logging.getLogger(__name__)

start_router = Router()

SESSION = 'session'


@start_router.message(F.text, CommandStart())
async def command_start(
        message: Message,
        dialog_manager: DialogManager
):

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    user_data = {}

    user_id: int = dialog_manager.event.from_user.id

    client: Client = await get_user(
        session=session,
        user_id=user_id,
        model=Client,
    )
    trainer: Trainer = await get_user(
        session=session,
        user_id=user_id,
        model=Trainer,
    )

    for user in (client, trainer):
        if user:
            if isinstance(user, Client):
                user_data.update(
                    ClientSchema(**user.get_data()).model_dump(),
                )
            if isinstance(user, Trainer):
                user_data.update(
                    TrainerSchema(**user.get_data()).model_dump(),
                )

    await dialog_manager.start(
        data=user_data,
        state=StartSG.main,
        mode=StartMode.RESET_STACK,
    )


@start_router.message(F.text == '/update')
async def update_window(
    message: Message,
    dialog_manager: DialogManager
):

    if dialog_manager.has_context():
        await dialog_manager.update(dialog_manager.dialog_data)
