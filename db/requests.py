from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities.context import Context

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from faker import Faker

from random import randint

from datetime import date

from db.models import (
    set_trainer,
    set_client,
    set_work_day,
    set_trainer_schedule,
    set_schedule,
    Trainer,
    Client,
    WorkingDay,
    TrainerSchedule,
    Schedule
)


OFFSET = 'offset'
LIMIT = 'limit'
SESSION = 'session'
ID = 'id'
WORKOUT = 'workout'
WORKOUTS = 'workouts'
SCHEDULES = 'schedules'
WORK = 'work'
RADIO_WORK = 'radio_work'
NAME = 'name'


async def get_user(
    session: AsyncSession,
    user_id: int,
    model: Client | Trainer
) -> Trainer | Client:

    user = await session.get(model, user_id)

    return user


async def add_trainer(
    id: int,
    name: str,
    dialog_manager: DialogManager
) -> None:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    user: Trainer = set_trainer(id=id, name=name)
    work_day1: WorkingDay = \
        set_work_day(1, ','.join(map(str, range(9, 18))), id)
    work_day2: WorkingDay = \
        set_work_day(2, ','.join(map(str, range(10, 20))), id)
    work_day3: WorkingDay = \
        set_work_day(3, ','.join(map(str, range(10, 22))), id)

    session.add_all(
        [user, work_day1, work_day2, work_day3]
    )
    await session.commit()


async def add_client(
    dialog_manager: DialogManager,
    trainer_id: int
) -> None:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    id: int = dialog_manager.event.from_user.id 
    name: str = dialog_manager.event.from_user.full_name or 'no_name'
    user: Client = set_client(
        id,
        name,
        trainer_id
    )

    session.add(user)

    await session.commit()

    #fake = Faker(locale='ru_RU')

    #for id in range(100_000_000, 100_000_050):  # удалить
    #    user: Client = set_client(id, fake.name(), trainer_id)  # удалить
    #    user.workouts = randint(1, 10)
    #    session.add(user)  # удалить

    #await session.commit()  # удалить


async def update_workouts(dialog_manager: DialogManager) -> None:

    client_id = dialog_manager.start_data[ID]
    value = dialog_manager.start_data[WORKOUT] + \
        dialog_manager.start_data[WORKOUTS]

    if value < 0:
        value = 0

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    dialog_manager.start_data[WORKOUTS] = value
    dialog_manager.start_data[WORKOUT] = 0

    smtm = select(Client).where(client_id == Client.id)
    res = await session.execute(smtm)
    client = res.scalar()
    client.workouts = value

    await session.commit()


async def get_data_user(
    dialog_manager: DialogManager,
    model: Client | Trainer,
    id: int | None = None
) -> dict:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    id = id or dialog_manager.event.from_user.id

    data = {}

    user: Trainer | Client = await get_user(session, id, model)

    if user:
        data.update(user.get_data())

    return data


async def get_group(
    dialog_manager: DialogManager,
    all=True
) -> list[dict]:

    offset = dialog_manager.dialog_data.get(OFFSET)
    limit = dialog_manager.dialog_data.get(LIMIT)
    id = dialog_manager.event.from_user.id

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    if all:
        smtm = select(Client).where(
            Client.trainer_id == id
        ).order_by(Client.id).offset(offset).limit(limit)

    else:
        smtm = select(Client).where(
            Client.trainer_id == id, Client.workouts > 0
        ).order_by(Client.id).offset(offset).limit(limit)

    rows = await session.execute(smtm)
    group = [client.get_data() for client in rows.unique().scalars().all()]

    return group


async def get_work_days(
    dialog_manager: DialogManager
) -> list[WorkingDay]:

    id = dialog_manager.event.from_user.id

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    user: Trainer = await get_user(session, id, Trainer)
    working_days: list[WorkingDay] = user.working_days

    return working_days


async def update_working_day(
    dialog_manager: DialogManager,
    id: int,
    value: str
):

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    user_id: int = dialog_manager.event.from_user.id

    user: Trainer = await get_user(session, user_id, Trainer)

    work_days: list[WorkingDay] = user.working_days

    for work_day in work_days:
        if work_day.item == id:
            work_day.work = value

    await session.commit()


async def add_trainer_schedule(
    dialog_manager: DialogManager,
    data: dict
):

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    schedules: list[TrainerSchedule] = [
        set_trainer_schedule(
            date,
            dialog_manager.start_data[SCHEDULES][work_item],
            dialog_manager.event.from_user.id
        ) for date, work_item in data.items()
    ]

    session.add_all(schedules)

    await session.commit()


async def cancel_trainer_schedule(
    dialog_manager: DialogManager,
    date: str
):
    
    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    trainer_id: int = dialog_manager.event.from_user.id

    stmt = select(TrainerSchedule).where(
        TrainerSchedule.trainer_id == trainer_id,
        TrainerSchedule.date == date
    )

    res = await session.execute(stmt)
    trainer_schedule: TrainerSchedule = res.scalar()

    await session.delete(trainer_schedule)

    await session.commit()


async def add_training(
    dialog_manager: DialogManager,
    date: str,
    client_id: int,
    trainer_id: int,
    time: int
):
    
    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    schedule: Schedule = set_schedule(
        client_id,
        trainer_id,
        date,
        time
    )

    session.add(schedule)

    client: Client = await get_user(session, client_id, Client)
    client.workouts -= 1

    await session.commit()


async def cancel_training_db(
    dialog_manager: DialogManager,
    client_id: int,
    trainer_id: int,
    date: str,
    time: int
):
    
    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    stmt = select(Schedule).where(
        Schedule.client_id == client_id,
        Schedule.trainer_id == trainer_id,
        Schedule.date == date,
        Schedule.time == time 
    )
    
    res = await session.execute(stmt)
    schedule: Schedule = res.scalar()

    client: Client = schedule.client
    client.workouts += 1

    await session.delete(schedule)

    await session.commit()


async def get_trainings(
    dialog_manager: DialogManager,
    date: str,
    trainer_id: int = None
) -> list[dict]:
    
    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    user_id: int = trainer_id or dialog_manager.event.from_user.id

    smtm = select(Schedule).where(
        Schedule.trainer_id == user_id,
        Schedule.date == date
    ).order_by(Schedule.date)
    rows = await session.execute(smtm)

    result = []

    for row in rows.scalars().unique().all():
        name = row.client.name
        data = row.get_data()
        data.update({NAME: name})
        result.append(data)
        
    return result


async def get_trainer_schedules(
    dialog_manager: DialogManager,
    trainer_id: int = None
) -> list[dict]:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    today = date.today()

    user_id = trainer_id or dialog_manager.event.from_user.id

    user: Trainer = await get_user(session, user_id, Trainer)

    return [
        day.get_data() for day in user.schedules if date.fromisoformat(day.date) > today
    ]
