from aiogram_dialog import DialogManager
from aiogram.types import CallbackQuery

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload
from sqlalchemy import select

from datetime import date

from random import choice

from db.models import (
    set_trainer,
    set_client,
    set_work_day,
    set_workout,
    set_trainer_schedule,
    set_schedule,
    Trainer,
    Client,
    RelationUsers,
    Workout,
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
TRAINER_ID = 'trainer_id'


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

    trainer: Trainer = set_trainer(id=id, name=name)

    for item in range(1, 4):
        trainer.working_days.append(
            set_work_day(
                item=item,
                work=','.join(map(str, range(9, 18+item))),
                trainer_id=id
            )
        )

    session.add(trainer)
    await session.commit()


async def add_client(
    dialog_manager: DialogManager,
    trainer_id: int,
    client_id: int | None = None,
    name: str = 'No_name'
) -> Client:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    trainer: Trainer = await get_user(session, trainer_id, Trainer)

    if trainer is None:
        raise ValueError

    client_id: int = client_id or dialog_manager.event.from_user.id
    name: str = name
    #name: str = dialog_manager.event.from_user.full_name or name

    client: Client = set_client(id=client_id, name=name)
    workout: Workout = set_workout(
        trainer_id=trainer.id,
        workouts=3,
        client_id=client_id
    )
    client.workouts.append(workout)
    client.trainers.append(trainer)

    session.add(client)

    await session.commit()


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
        client_id=client_id
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
        session,
        dialog_manager.event.from_user.id,
        Trainer
    )

    ####Удалить####
    stmt = (
        select(Client)
        .join(RelationUsers)
        .where(RelationUsers.trainer_id == dialog_manager.event.from_user.id)
    )

    result = await session.execute(stmt)
    clients: list[Client] = result.scalars().all()
    ######Удалить########


    for date_, work_item in data.items():
        trainer_schedule: TrainerSchedule = set_trainer_schedule(
            date=date_,
            time=dialog_manager.start_data[SCHEDULES][work_item],
            trainer_id=trainer.id
        )
        trainer_schedule.trainer = trainer
        session.add(trainer_schedule)

        ######Удалить#######
        time = list(map(int, dialog_manager.start_data[SCHEDULES][work_item].split(',')))
        for t in time:
            if t % 2:
                continue
            client: Client = choice(clients)
            schedule: Schedule = set_schedule(
                client_id=client.id,
                trainer_id=trainer.id,
                date=date_,
                time=t
            )
            session.add(schedule)
            stmt = (
                select(Workout)
                .where(Workout.client_id == client.id)
            )
            result = await session.execute(stmt)
            workout: Workout = result.scalar()
            workout.workouts -= 1
        #####Удалить#######

    await session.commit()


async def cancel_trainer_schedule(
    dialog_manager: DialogManager,
    date: str
):

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    trainer_id: int = dialog_manager.event.from_user.id

    stmt = (
        select(TrainerSchedule)
        .where(
            TrainerSchedule.trainer_id == trainer_id,
            TrainerSchedule.date == date
        )
    )

    res = await session.execute(stmt)
    trainer_schedule: TrainerSchedule = res.scalar()

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

    schedule: Schedule = set_schedule(
        client_id=client_id,
        trainer_id=trainer_id,
        date=date_,
        time=time_
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

        for schedule in client.schedules:  # scheduke
            if (schedule.trainer_id == trainer_id
                and schedule.date == date_
                    and schedule.time == time_):
                await session.delete(schedule)
                break

        await session.commit()


async def get_clients_training(
    dialog_manager: DialogManager,
    date: str,
    trainer_id: int = None
) -> list[dict]:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    trainer_id: int = trainer_id or dialog_manager.event.from_user.id

    stmt = (
        select(Client, Schedule)
        .join(Schedule)
        .where(
            Schedule.trainer_id == trainer_id,
            Schedule.date == date
        )
        .order_by(Schedule.time)
    )

    result = await session.execute(stmt)

    data_trainings = []
    if result:
        for client, schedule in result.all():
            data: dict = schedule.get_data()
            data.update({NAME: client.name})
            data_trainings.append(data)

    return data_trainings


async def get_trainer_schedules(
    dialog_manager: DialogManager,
    trainer_id: int = None
) -> list[TrainerSchedule]:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    today = date.today().isoformat()
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
        if schedule.date > today
    ]

    return schedules


async def get_schedule(
    dialog_manager: DialogManager,
    date: str,
    time: int,
    trainer_id: int
) -> Schedule | None:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    stmt = select(Schedule).where(
        Schedule.trainer_id == trainer_id,
        Schedule.date == date,
        Schedule.time == time
    )

    result = await session.execute(stmt)

    return result.scalar_one_or_none()


async def get_schedules(
    dialog_manager: DialogManager,
    trainer_id: int
) -> list[Schedule]:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    today: str = date.today().isoformat()

    stmt = (
        select(Schedule)
        .where(
            Schedule.trainer_id == trainer_id,
            Schedule.date >= today)
    )

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_client_trainings(
    dialog_manager: DialogManager,
    trainer_id: int,
    client_id: int
) -> list[Schedule] | None:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    today: str = date.today().isoformat()

    stmt = (
        select(Schedule)
        .where(
            Schedule.trainer_id == trainer_id,
            Schedule.client_id == client_id,
            Schedule.date > today
        )
    )

    result = await session.execute(stmt)

    if result:
        return result.scalars().all()


async def get_trainers(
    dialog_manager: DialogManager
) -> list[Trainer]:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    ####### Удалить#####
    trainer: Trainer = set_trainer(123123123, 'dfdfg')
    client: Client = await get_user(session, dialog_manager.event.from_user.id, Client)
    trainer.clients.append(client)
    session.add(trainer)
    await session.commit()
    ###### Удалить########

    client_id: int = dialog_manager.event.from_user.id

    stmt = (
        select(Client)
        .where(Client.id == client_id)
        .options(selectinload(Client.trainers))
    )

    result = await session.execute(stmt)

    if result:
        return result.scalar().trainers
