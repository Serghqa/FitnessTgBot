from aiogram_dialog import DialogManager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from faker import Faker

from datetime import date

from db.models import (
    set_trainer,
    set_client,
    set_work_day,
    set_trainer_schedule,
    Trainer,
    Client,
    WorkingDay,
    TrainerSchedule
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
    name = dialog_manager.event.from_user.full_name or 'no_name'

    user: Trainer = set_trainer(id=id, name=name)
    work_day1: WorkingDay = set_work_day(user, 1, ', '.join(map(str, range(9, 18))))
    work_day2: WorkingDay = set_work_day(user, 2, ', '.join(map(str, range(10, 20))))
    work_day3: WorkingDay = \
        set_work_day(user, 3, ', '.join(map(str, range(10, 22))))

    session.add_all(
        [user, work_day1, work_day2, work_day3]
    )
    await session.commit()


async def add_client(dialog_manager: DialogManager, trainer_id: int) -> None:

    session: AsyncSession = dialog_manager.middleware_data.get('session')

    fake = Faker(locale='ru_RU')

    for i in range(100_000_000, 100_000_050):  # удалить
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
        'trainer_id': None
    }

    user = await get_user(session, id, model)

    if user:
        data.update(user.get_data())

    return data


async def get_group(dialog_manager: DialogManager, all=True) -> list[dict]:

    offset = dialog_manager.dialog_data.get('offset')
    limit = dialog_manager.dialog_data.get('limit')
    id = dialog_manager.event.from_user.id

    session: AsyncSession = dialog_manager.middleware_data.get('session')

    if all:
        smtm = select(Client).filter(
            Client.trainer_id == id
        ).order_by(Client.id).offset(offset).limit(limit)

    else:
        smtm = select(Client).filter(
            Client.trainer_id == id, Client.workouts > 0
        ).order_by(Client.id).offset(offset).limit(limit)

    rows = await session.execute(smtm)
    group = [row.Client.get_data() for row in rows.all()]

    return group


async def get_work_days(
    dialog_manager: DialogManager
) -> list[WorkingDay]:

    id = dialog_manager.event.from_user.id

    session: AsyncSession = dialog_manager.middleware_data.get('session')

    user: Trainer = await get_user(session, id, Trainer)
    daily_schedules: list[WorkingDay] = user.working_days

    return daily_schedules


async def update_working_day(dialog_manager: DialogManager, id: int, value: str):

    session: AsyncSession = dialog_manager.middleware_data.get('session')

    schedule: WorkingDay = await session.get(WorkingDay, id)

    schedule.work = value

    await session.commit()


async def add_trainer_schedule(dialog_manager: DialogManager, data: dict):

    session: AsyncSession = dialog_manager.middleware_data.get('session')

    working_days: dict[int, dict] = dialog_manager.start_data['schedules']

    schedules: list[TrainerSchedule] = [
        set_trainer_schedule(
            date,
            working_days[int(work_item)]['work'],
            dialog_manager.event.from_user.id
        ) \
            for date, work_item in data.items() if work_item
    ]

    session.add_all(schedules)

    await session.commit()


async def get_trainer_schedules(dialog_manager: DialogManager) -> list[dict]:

    session: AsyncSession = dialog_manager.middleware_data.get('session')

    today = date.today()

    user_id = dialog_manager.event.from_user.id

    user: Trainer = await get_user(session, user_id, Trainer)

    return [day.get_data() for day in user.schedules if date.fromisoformat(day.date) > today]
