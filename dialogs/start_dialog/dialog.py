import logging

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiogram_dialog import (
    DialogManager,
    StartMode
)
from states import StartSG


logger = logging.getLogger(__name__)

start_router = Router()


@start_router.message(F.text, CommandStart())
async def command_start(
        message: Message,
        dialog_manager: DialogManager
):
    await dialog_manager.start(
        state=StartSG.start,
        mode=StartMode.RESET_STACK
    )
