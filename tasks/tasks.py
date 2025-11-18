import logging

from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker
from taskiq import Context, TaskiqDepends
from typing import Annotated
from zoneinfo import ZoneInfo

from db import Schedule, TrainerSchedule
from taskiq_broker import broker


logger = logging.getLogger(__name__)


@broker.task(task_name='send_scheduled_notification')
async def send_scheduled_notification(
    chat_id: int,
    message_text: str,
    context: Annotated[Context, TaskiqDepends()]
):

    bot: Bot = context.broker.custom_dependency_context.get('bot')

    try:
        await bot.send_message(chat_id, message_text)

    except TelegramForbiddenError as error:
        logger.warning('Ошибка, сообщение не удалось отправить. %s', error)


@broker.task(task_name='clear_old_data')
async def clear_old_data(
    context: Annotated[Context, TaskiqDepends()]
):

    session: async_sessionmaker = \
        context.broker.custom_dependency_context.get('session')

    async with session() as session:

        date_ = datetime.now(ZoneInfo('UTC')).date()
        stmt = (
            select(Schedule)
            .where(Schedule.date < date_)
        )

        result = await session.execute(stmt)
        for schedule in result.scalars():
            await session.delete(schedule)
        logger.info('Устаревшие данные из таблицы Schedule очищены')
        stmt = (
            select(TrainerSchedule)
            .where(TrainerSchedule.date < date_)
        )
        result = await session.execute(stmt)
        for trainer_schedule in result.scalars():
            await session.delete(trainer_schedule)
        logger.info('Устаревшие данные из таблицы TrainerSchedule очищены')
        await session.commit()
