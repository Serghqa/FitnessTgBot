import logging

from aiogram.types import CallbackQuery

from aiogram_dialog import DialogManager

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from datetime import datetime

from db.models import (
    Client,
    Schedule,
    set_client,
    set_schedule,
    set_trainer,
    set_trainer_schedule,
    set_workout,
    set_work_day,
    Trainer,
    TrainerSchedule,
    Workout,
    WorkingDay,
)
from schemas import ScheduleSchema
from timezones import get_current_date


logger = logging.getLogger(__name__)

DATE = 'date'
ID = 'id'
LIMIT = 'limit'
NAME = 'name'
OFFSET = 'offset'
RADIO_WORK = 'radio_work'
SCHEDULES = 'schedules'
SESSION = 'session'
TIME = 'time'
TIME_ZONE = 'time_zone'
TRAINER_ID = 'trainer_id'
UTC = 'UTC'
WORK = 'work'
WORKOUT = 'workout'
WORKOUTS = 'workouts'


async def get_user(
    session: AsyncSession,
    user_id: int,
    model: Client | Trainer
) -> Trainer | Client | None:

    user = await session.get(model, user_id)

    return user


async def get_client_db(
    dialog_manager: DialogManager,
    client_id: int,
    trainer_id: int
) -> Client | None:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    stmt = (
        select(Client, Trainer)
        .where(
            Client.id == client_id,
            Trainer.id == trainer_id,
        )
        .options(selectinload(Client.workouts))
    )

    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def add_trainer(
    id: int,
    name: str,
    dialog_manager: DialogManager,
    time_zone: str
) -> Trainer:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    trainer: Trainer = set_trainer(id=id, name=name, time_zone=time_zone)

    for item in range(1, 4):
        trainer.working_days.append(
            set_work_day(
                item=item,
                work=','.join(map(str, range(9, 18+item))),
                trainer_id=id,
            )
        )

    session.add(trainer)
    await session.commit()

    return trainer


async def add_client(
    dialog_manager: DialogManager,
    trainer_id: int,
    client_id: int,
    name: str,
) -> Client:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    trainer: Trainer = await get_user(
        session=session,
        user_id=trainer_id,
        model=Trainer,
    )

    if trainer is None:
        raise ValueError

    dialog_manager.dialog_data[TIME_ZONE] = trainer.time_zone

    client: Client = set_client(id=client_id, name=name)
    workout: Workout = set_workout(
        trainer_id=trainer.id,
        workouts=0,
        client_id=client_id,
    )
    client.workouts.append(workout)
    client.trainers.append(trainer)

    session.add(client)

    await session.commit()

    return client


async def update_workouts(
    dialog_manager: DialogManager,
    callback: CallbackQuery
) -> None:

    client_id: int = dialog_manager.start_data[ID]
    trainer_id: int = dialog_manager.event.from_user.id
    workouts: int = dialog_manager.start_data[WORKOUTS]

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    workout: Workout = await get_workouts(
        dialog_manager=dialog_manager,
        trainer_id=trainer_id,
        client_id=client_id,
    )

    if workout.workouts == workouts:
        workout.workouts = workouts + dialog_manager.start_data[WORKOUT]
        await session.commit()

    else:
        await callback.answer(
            text=(
                'Во время редактирования, клиент '
                'производил операции связанные с записью, '
                'данные были измененны. '
                'Повторите вашу операцию еще раз, пожалуйста!'
            ),
            show_alert=True,
        )

    dialog_manager.start_data[WORKOUTS] = workout.workouts
    dialog_manager.start_data[WORKOUT] = 0


async def get_group(
    dialog_manager: DialogManager,
    all=True
) -> list[dict]:

    offset: int = dialog_manager.dialog_data.get(OFFSET, 1)
    limit: int = dialog_manager.dialog_data.get(LIMIT, 10)
    id: int = dialog_manager.event.from_user.id

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    if all:
        stmt = (
            select(Client, Workout)
            .join(Client.trainers)
            .join(Workout)
            .where(Trainer.id == id)
            .order_by(Client.id)
            .offset(offset)
            .limit(limit)
        )

    else:
        stmt = (
            select(Client, Workout)
            .join(Client.trainers)
            .join(Workout)
            .where(Trainer.id == id, Workout.workouts > 0)
            .order_by(Client.id)
            .offset(offset)
            .limit(limit)
        )

    result = await session.execute(stmt)

    group: list[dict] = [
        {
            'id': client.id,
            'name': client.name,
            'workouts': workout.workouts
        }
        for client, workout in result
    ]

    return group


async def get_workouts(
    dialog_manager: DialogManager,
    trainer_id: int,
    client_id: int
) -> Workout:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    stmt = (
        select(Workout)
        .where(
            Workout.client_id == client_id,
            Workout.trainer_id == trainer_id
        )
    )

    result = await session.execute(stmt)

    return result.scalar()


async def get_work_days(
    dialog_manager: DialogManager
) -> list[WorkingDay]:

    id = dialog_manager.event.from_user.id

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    stmt = (
        select(Trainer)
        .where(Trainer.id == id)
        .options(selectinload(Trainer.working_days))
    )

    result = await session.scalar(stmt)
    working_days: list[WorkingDay] = result.working_days

    return working_days


async def update_working_day(
    dialog_manager: DialogManager,
    id: int,
    value: str
):

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    work_days: list[WorkingDay] = await get_work_days(dialog_manager)

    for work_day in work_days:
        if work_day.item == id:
            work_day.work = value
            break

    await session.commit()


async def add_trainer_schedule(
    dialog_manager: DialogManager,
    data: dict
):

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    trainer: Trainer = await get_user(
        session=session,
        user_id=dialog_manager.event.from_user.id,
        model=Trainer,
    )

    for date_, work_item in data.items():
        dt = datetime.fromisoformat(date_)
        trainer_schedule: TrainerSchedule = set_trainer_schedule(
            date=dt.date(),
            time=dialog_manager.start_data[SCHEDULES][work_item],
            trainer_id=trainer.id,
        )
        trainer_schedule.trainer = trainer
        session.add(trainer_schedule)

    await session.commit()


async def cancel_trainer_schedule(
    dialog_manager: DialogManager,
    date_: str
):

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    dt = datetime.fromisoformat(date_)
    trainer_id: int = dialog_manager.event.from_user.id

    stmt = (
        select(TrainerSchedule)
        .where(
            TrainerSchedule.trainer_id == trainer_id,
            TrainerSchedule.date == dt.date(),
        )
    )

    result = await session.execute(stmt)

    if result:
        trainer_schedule: TrainerSchedule = result.scalar()

        await session.delete(trainer_schedule)

        await session.commit()


async def add_training(
    dialog_manager: DialogManager,
    date_: str,
    client_id: int,
    trainer_id: int,
    time_: int
) -> Schedule:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    dt = datetime.fromisoformat(date_)

    ScheduleSchema(
        client_id=client_id,
        trainer_id=trainer_id,
        date=dt.date(),
        time=time_,
    )

    schedule: Schedule = set_schedule(
        client_id=client_id,
        trainer_id=trainer_id,
        date=dt.date(),
        time=time_,
    )

    stmt = (
        select(Client)
        .where(Client.id == client_id)
        .options(selectinload(Client.trainers))
        .options(selectinload(Client.workouts))
    )

    client: Client = await session.scalar(stmt)

    for trainer in client.trainers:  # Trainer
        if trainer.id == trainer_id:
            schedule.trainer = trainer
            break

    for workout in client.workouts:
        if workout.client_id == client_id:
            workout.workouts -= 1
            dialog_manager.start_data[WORKOUTS] = workout.workouts
            break

    schedule.client = client

    session.add(schedule)

    await session.commit()

    return schedule


async def cancel_training_db(
    dialog_manager: DialogManager,
    client_id: int,
    trainer_id: int,
    date_: str,
    time_: int
):

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    dt = datetime.fromisoformat(date_)

    stmt = (
        select(Client)
        .where(Client.id == client_id)
        .options(selectinload(Client.schedules))
        .options(selectinload(Client.workouts))
    )

    result = await session.execute(stmt)
    if result:
        client: Client = result.scalar()

        for workout in client.workouts:  # Workout
            if workout.trainer_id == trainer_id:
                workout.workouts += 1
                dialog_manager.start_data[WORKOUTS] = workout.workouts
                break

        for schedule in client.schedules:  # Schedule
            if (schedule.trainer_id == trainer_id
                and schedule.date == dt.date()
                    and schedule.time == time_):
                await session.delete(schedule)
                break

        await session.commit()


async def get_clients_training(
    dialog_manager: DialogManager,
    date_: str,
    trainer_id: int = None
) -> list[dict]:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    dt = datetime.fromisoformat(date_)
    trainer_id: int = trainer_id or dialog_manager.event.from_user.id

    stmt = (
        select(Client, Schedule)
        .join(Schedule)
        .where(
            Schedule.trainer_id == trainer_id,
            Schedule.date == dt.date(),
        )
        .order_by(Schedule.time)
    )

    result = await session.execute(stmt)

    data_trainings = []
    if result:
        for client, schedule in result.all():  # Client, Schedule
            data = {}
            data.update(client.get_data())
            data[TRAINER_ID] = schedule.trainer_id
            data[DATE] = schedule.date.isoformat()
            data[TIME] = schedule.time
            data_trainings.append(data)

    return data_trainings


async def get_trainer_schedules(
    dialog_manager: DialogManager,
    trainer_id: int = None
) -> list[TrainerSchedule]:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_date(timezone)

    trainer_id = trainer_id or dialog_manager.event.from_user.id

    stmt = (
        select(Trainer)
        .where(Trainer.id == trainer_id)
        .options(selectinload(Trainer.trainer_schedules))
    )

    result = await session.execute(stmt)
    trainer: Trainer = result.scalar()

    schedules: list[TrainerSchedule] = [
        schedule for schedule in trainer.trainer_schedules
        if schedule.date > today.date()
    ]

    return schedules


async def get_schedule(
    dialog_manager: DialogManager,
    date_: str,
    time_: int,
    trainer_id: int
) -> Schedule | None:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    dt = datetime.fromisoformat(date_)

    stmt = select(Schedule).where(
        Schedule.trainer_id == trainer_id,
        Schedule.date == dt.date(),
        Schedule.time == time_
    )

    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def get_schedules(
    dialog_manager: DialogManager,
    trainer_id: int
) -> list[Schedule]:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_date(timezone)

    stmt = (
        select(Schedule)
        .where(
            Schedule.trainer_id == trainer_id,
            Schedule.date >= today.date()
        )
    )

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_client_trainings(
    dialog_manager: DialogManager,
    trainer_id: int,
    client_id: int
) -> list[Schedule]:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_date(timezone)

    stmt = (
        select(Schedule)
        .where(
            Schedule.trainer_id == trainer_id,
            Schedule.client_id == client_id,
            Schedule.date > today.date()
        )
    )

    result = await session.execute(stmt)

    if result:
        return result.scalars().all()


async def get_trainers(
    dialog_manager: DialogManager,
) -> list[Trainer] | None:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    client_id: int = dialog_manager.event.from_user.id

    stmt = (
        select(Client)
        .where(Client.id == client_id)
        .options(selectinload(Client.trainers))
    )

    result: Client | None = await session.scalar(stmt)

    if result is not None:
        return result.trainers
