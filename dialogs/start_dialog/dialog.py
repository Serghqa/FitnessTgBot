import asyncio
import logging

from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram_dialog import (
    DialogManager,
    StartMode,
)
from sqlalchemy.exc import SQLAlchemyError

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

    user_data = {}

    user_id: int = dialog_manager.event.from_user.id

    try:
        client: Client | None
        trainer: Trainer | None

        client, trainer = await asyncio.gather(
            get_user(
                dialog_manager=dialog_manager,
                user_id=user_id,
                model=Client,
            ),
            get_user(
                dialog_manager=dialog_manager,
                user_id=user_id,
                model=Trainer,
            )
        )
    except SQLAlchemyError as error:
        logger.error(
            'Ошибка при попытке получить объект Trainer или Client, '
            'user_id=%s, path=%s',
            user_id, __name__,
            exc_info=error,
        )

        await message.answer(
            text='Произошла неожиданная ошибка, обратитесь в поддержку.'
        )
        return

    for user in (client, trainer):
        if user:
            if isinstance(user, Client):
                user_data.update(
                    ClientSchema.model_validate(user.get_data()).model_dump(),
                )
            elif isinstance(user, Trainer):
                user_data.update(
                    TrainerSchema.model_validate(user.get_data()).model_dump(),
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
