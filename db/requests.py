from aiogram_dialog import DialogManager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from faker import Faker

from db.models import (
    set_trainer,
    set_client,
    set_daily_schedule,
    Trainer,
    Client,
    DailySchedule
)
from typing import Any


async def get_user(
    session: AsyncSession,
    user_id: int,
    model: Client | Trainer
) -> Trainer | Client:

    user = await session.get(model, user_id)

    return user


async def add_trainer(dialog_manager: DialogManager) -> None:

    session: AsyncSession = dialog_manager.middleware_data.get('session')

    id = dialog_manager.event.from_user.id
    name = dialog_manager.event.from_user.id or 'no_name'

    user: Trainer = set_trainer(id=id, name=name)
    daily_schedule_1: DailySchedule = \
        set_daily_schedule(user, 1, ', '.join(map(str, range(9, 18))))
    daily_schedule_2: DailySchedule = \
        set_daily_schedule(user, 2, ', '.join(map(str, range(10, 20))))
    daily_schedule_3: DailySchedule = \
        set_daily_schedule(user, 3, ', '.join(map(str, range(10, 22))))

    session.add_all(
        [user, daily_schedule_1, daily_schedule_2, daily_schedule_3]
    )
    await session.commit()


async def add_client(dialog_manager: DialogManager, trainer_id: int) -> None:

    session: AsyncSession = dialog_manager.middleware_data.get('session')

    fake = Faker(locale='ru_RU')

    for i in range(100_000_000, 100_001_000):  # удалить
        user: Client = set_client(i, fake.name(), trainer_id)  # удалить
        session.add(user)  # удалить

    await session.commit()  # удалить


async def update_workouts(dialog_manager: DialogManager) -> None:

    client_id = dialog_manager.start_data['id']
    value = dialog_manager.start_data['workout'] + \
        dialog_manager.start_data['workouts']

    if value < 0:
        value = 0

    session: AsyncSession = dialog_manager.middleware_data.get('session')

    dialog_manager.start_data['workouts'] = value
    dialog_manager.start_data['workout'] = 0

    stmt = select(Client).filter(client_id == Client.id)
    res = await session.execute(stmt)
    client = res.scalar()
    client.workouts = value

    await session.commit()


async def get_data_user(
    dialog_manager: DialogManager,
    model: Client | Trainer,
    id: int | None = None
) -> dict[str, Any]:

    session: AsyncSession = dialog_manager.middleware_data.get('session')
    id = id or dialog_manager.event.from_user.id

    data = {
        'client': None,
        'trainer': None,
        'id': None,
        'name': None,
        'workouts': None,
        'trainer_id': None,
        'radio_default': '1'
    }

    user = await get_user(session, id, model)

    if user:
        data.update(user.get_data())

    return data


async def get_group(dialog_manager: DialogManager) -> list[dict]:

    offset = dialog_manager.dialog_data.get('offset')
    limit = dialog_manager.dialog_data.get('limit')
    id = dialog_manager.event.from_user.id

    session: AsyncSession = dialog_manager.middleware_data.get('session')

    smtm = select(Client).filter(
        Client.trainer_id == id
    ).order_by(Client.id).offset(offset).limit(limit)

    rows = await session.execute(smtm)
    group = [row.Client.get_data() for row in rows.all()]

    return group


async def get_daily_schedules(
    dialog_manager: DialogManager
) -> list[DailySchedule]:

    id = dialog_manager.event.from_user.id

    session: AsyncSession = dialog_manager.middleware_data.get('session')

    user: Trainer = await get_user(session, id, Trainer)
    daily_schedules: list[DailySchedule] = user.daily_schedules

    return daily_schedules


async def update_daily_schedule(dialog_manager: DialogManager, id: int, value: str):

    session: AsyncSession = dialog_manager.middleware_data.get('session')

    schedule: DailySchedule = await session.get(DailySchedule, id)

    schedule.work = value

    await session.commit()
