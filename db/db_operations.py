import logging

from aiogram_dialog import DialogManager
from datetime import datetime
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db import (
    Client,
    RelationUsers,
    set_relation_users,
    Schedule,
    set_schedule,
    set_trainer_schedule,
    set_work_day,
    Trainer,
    TrainerSchedule,
    Workout,
    WorkingDay,
)
from schemas import ScheduleSchema
from timezones import get_current_datetime


logger = logging.getLogger(__name__)

CLIENT_ID = 'client_id'
DATE = 'date'
ID = 'id'
IS_WORK = 'is_work'
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


async def relation_exists_trainer_client(
    dialog_manager: DialogManager,
    client_id: int,
    trainer_id: int
) -> bool:
    """
    Проверяет существование связи между Trainer и Client.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    stmt = (
        select(
            exists()
            .where(
                RelationUsers.client_id == client_id,
                RelationUsers.trainer_id == trainer_id
            )
        )
    )

    result = await session.execute(stmt)

    return result.scalar()


async def get_schedule_exsists(
    dialog_manager: DialogManager,
    selected_date: str,
    selected_time: int,
    trainer_id: int
) -> bool:
    """
    Функция используется для проверки существования записи.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    dt = datetime.fromisoformat(selected_date)

    stmt = (
        select(
            exists()
            .where(
                Schedule.trainer_id == trainer_id,
                Schedule.date == dt.date(),
                Schedule.time == selected_time
            )
        )
    )

    result = await session.execute(stmt)

    return result.scalar()


async def get_user(
    dialog_manager: DialogManager,
    user_id: int,
    model: Client | Trainer
) -> Trainer | Client | None:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    user = await session.get(model, user_id)

    return user


async def get_client_db(
    dialog_manager: DialogManager,
    client_id: int,
    trainer_id: int
) -> Client | None:
    """
    Асинхронно извлекает данные клиента.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    stmt = (
        select(Client)
        .join(RelationUsers, Client.id == RelationUsers.client_id)
        .where(
            trainer_id == RelationUsers.trainer_id,
            client_id == Client.id
        )
        .options(selectinload(Client.workouts))
    )

    result: Client | None = await session.scalar(stmt)

    return result


async def add_workout(
    dialog_manager: DialogManager,
    workout: Workout
) -> Workout:
    """
    Добавляет объект Workout с связанным клиентом
    в базу данных, устанавливает связь клиента с
    тренером.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    relation_users: RelationUsers = set_relation_users(
        trainer_id=workout.trainer_id,
        client_id=workout.client_id,
    )

    session.add_all([workout, relation_users])

    await session.commit()

    return workout


async def add_trainer(
    trainer: Trainer,
    dialog_manager: DialogManager,
) -> Trainer:
    """
    Создаёт нового тренера в базе данных вместе с тремя расписаниями рабочих
    дней по умолчанию.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    for item in range(1, 4):
        working_day: WorkingDay = set_work_day(
            item=str(item),
            work=','.join(map(str, range(9, 18+item))),
            trainer_id=trainer.id,
        )
        trainer.working_days.append(working_day)

    session.add(trainer)
    await session.commit()

    return trainer


async def add_client(
    dialog_manager: DialogManager,
    trainer: Trainer,
    client: Client,
    workout: Workout
) -> Client:
    """
    Добавляет нового клиента в систему, связывает его с тренером и
    инициализирует счётчик тренировок.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    client.workouts.append(workout)
    client.trainers.append(trainer)
    session.add(client)
    await session.commit()

    return client


async def update_workouts(
    workout: Workout,
    workouts: int,
    dialog_manager: DialogManager
) -> Workout | None:
    """
    Обновляет количество тренировок клиента в базе данных.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    workout.workouts = workouts
    await session.commit()

    return workout


async def get_frame_clients(
    dialog_manager: DialogManager,
    all=True
) -> list[dict]:
    """
    Асинхронно извлекает постраничный список клиентов, связанных с
    текущим тренером.
    """

    offset: int = dialog_manager.dialog_data.get(OFFSET, 0)
    limit: int = dialog_manager.dialog_data.get(LIMIT, 5)
    trainer_id: int = dialog_manager.event.from_user.id

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    if all:
        stmt = (
            select(Client, Workout)
            .join(Client.trainers)
            .join(Workout)
            .where(Trainer.id == trainer_id)
            .order_by(Client.id)
            .offset(offset)
            .limit(limit)
        )

    else:
        stmt = (
            select(Client, Workout)
            .join(Client.trainers)
            .join(Workout)
            .where(Trainer.id == trainer_id, Workout.workouts > 0)
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
) -> Workout | None:
    """
    Асинхронно извлекает объект ORM-тренировки для конкретного
    клиента и тренера.
    """

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
) -> list[WorkingDay] | None:
    """
    Асинхронно извлекает список рабочих смен (WorkingDay) тренера по его ID.
    """

    trainer_id = dialog_manager.event.from_user.id

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    stmt = (
        select(Trainer)
        .where(Trainer.id == trainer_id)
        .options(selectinload(Trainer.working_days))
    )
    trainer: Trainer = await session.scalar(stmt)
    if trainer is not None:
        working_days: list[WorkingDay] = trainer.working_days
        if working_days:
            return working_days
    return None


async def update_working_day(
    dialog_manager: DialogManager,
    item: str,
    value: str
) -> WorkingDay | None:
    """
    Обновляет расписание (work) для конкретной рабочей смены (WorkingDay)
    тренера.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    trainer_id: int = dialog_manager.event.from_user.id

    stmt = (
        select(WorkingDay)
        .where(
            WorkingDay.trainer_id == trainer_id,
            WorkingDay.item == item
        )
    )
    result = await session.execute(stmt)
    work_day = result.scalar()

    if work_day is not None:
        work_day.work = value

        await session.commit()

    return work_day


async def add_trainer_schedule(
    dialog_manager: DialogManager,
    trainer_schedules: dict,
    work_schedules: dict
) -> None:
    """
    Добавляет расписания тренера в базу данных на
    основе предоставленного словаря.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    trainer_id: int = dialog_manager.event.from_user.id

    for date_selected, work_item in trainer_schedules.items():
        dt = datetime.fromisoformat(date_selected)
        trainer_schedule: TrainerSchedule = set_trainer_schedule(
            date=dt.date(),
            time=work_schedules[work_item],
            trainer_id=trainer_id,
        )
        session.add(trainer_schedule)

    await session.commit()


async def add_training(
    dialog_manager: DialogManager,
    selected_date: str,
    selected_time: int,
    client_id: int,
    trainer_id: int
) -> Schedule | None:
    """
    Создает запись о тренировке
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    dt = datetime.fromisoformat(selected_date)

    schedule_schema: ScheduleSchema = ScheduleSchema(
        client_id=client_id,
        trainer_id=trainer_id,
        date=dt.date(),
        time=selected_time,
    )

    schedule: Schedule = set_schedule(
        client_id=schedule_schema.client_id,
        trainer_id=schedule_schema.trainer_id,
        date=schedule_schema.date,
        time=schedule_schema.time,
    )

    stmt = (
        select(Client)
        .where(Client.id == client_id)
        .options(selectinload(Client.trainers))
        .options(selectinload(Client.workouts))
    )

    client: Client = await session.scalar(stmt)
    if client is None:
        return

    trainer = None
    for tr in client.trainers:  # Trainer
        if tr.id == trainer_id:
            schedule.trainer = tr
            trainer = tr
            break
    if trainer is None:
        return

    workout = None
    for wrk in client.workouts:
        if wrk.client_id == client_id:
            wrk.workouts -= 1
            workout = wrk
            break
    if workout is None:
        return

    schedule.client = client

    session.add(schedule)

    await session.commit()

    return schedule


async def cancel_training_db(
    dialog_manager: DialogManager,
    selected_date: str,
    trainer_id: int,
    trainings: list[dict]
) -> list[dict] | None:
    """
    Отменяет записи на тренировку.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    dt: datetime = datetime.fromisoformat(selected_date)

    canceled_trainings = []
    is_work: bool = dialog_manager.dialog_data.get(IS_WORK, False)

    for training in trainings:
        stmt_schedule = (
            select(Schedule)
            .where(
                Schedule.client_id == training[CLIENT_ID],
                Schedule.trainer_id == trainer_id,
                Schedule.date == dt.date(),
                Schedule.time == training[TIME]
            )
        )

        stmt_workout = (
            select(Workout)
            .where(
                Workout.client_id == training[CLIENT_ID],
                Workout.trainer_id == trainer_id,
            )
        )

        result_schedule = await session.execute(stmt_schedule)
        result_workout = await session.execute(stmt_workout)
        schedule: Schedule = result_schedule.scalar_one_or_none()
        workout: Workout = result_workout.scalar_one_or_none()
        if schedule and workout:
            workout.workouts += 1
            canceled_trainings.append(
                {'schedule': schedule, 'workout': workout}
            )
            await session.delete(schedule)
        else:
            return

    if is_work:
        stmt_trainer_schedule = (
            select(TrainerSchedule)
            .where(
                TrainerSchedule.trainer_id == trainer_id,
                TrainerSchedule.date == dt.date(),
            )
        )
        result_trainer_schedule = await session.execute(
            stmt_trainer_schedule
        )
        trainer_schedule: TrainerSchedule = \
            result_trainer_schedule.scalar_one_or_none()
        if trainer_schedule:
            await session.delete(trainer_schedule)
            if IS_WORK in dialog_manager.dialog_data:
                del dialog_manager.dialog_data[IS_WORK]
        else:
            return

    await session.commit()

    return canceled_trainings


async def get_clients_training(
    dialog_manager: DialogManager,
    date_: str,
    trainer_id: None | int = None
) -> list[tuple[Client, Schedule]]:
    """
   Получает список клиентов и их расписания тренировок на указанный
   день для тренера.
    """

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
    trainings: list[tuple[Client, Schedule]] = result.all()

    return trainings


async def get_trainer_schedules(
    dialog_manager: DialogManager,
    trainer_id: int = None
) -> list[TrainerSchedule]:
    """
    Функция извлекает из базы данных все записи расписания тренера,
    дата которых строго больше текущей даты, учитывая часовой
    пояс пользователя.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_datetime(timezone)

    trainer_id = trainer_id or dialog_manager.event.from_user.id

    stmt = (
        select(TrainerSchedule)
        .join(Trainer)
        .where(
            Trainer.id == trainer_id,
            TrainerSchedule.date >= today.date()
        )
        .order_by(TrainerSchedule.date)
    )
    result = await session.execute(stmt)
    schedules: list[TrainerSchedule] = result.scalars().all()

    return schedules


async def get_trainer_schedule(
    dialog_manager: DialogManager,
    trainer_id: int,
    selected_date: str
) -> TrainerSchedule | None:
    """
    Получает расписание тренировок тренера на указанную дату.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    dt: datetime = datetime.fromisoformat(selected_date)

    stmt = (
        select(TrainerSchedule)
        .where(
            TrainerSchedule.trainer_id == trainer_id,
            TrainerSchedule.date == dt.date()
        )
    )

    result = await session.execute(stmt)

    return result.scalar()


async def get_schedules(
    dialog_manager: DialogManager,
    trainer_id: int
) -> list[Schedule]:

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_datetime(timezone)

    stmt = (
        select(Schedule)
        .where(
            Schedule.trainer_id == trainer_id,
            Schedule.date > today.date()
        )
    )

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_client_trainings(
    dialog_manager: DialogManager,
    trainer_id: int,
    client_id: int
) -> list[Schedule]:
    """
    Асинхронная функция для получения списка будущих
    тренировок клиента у конкретного тренера.
    """

    session: AsyncSession = dialog_manager.middleware_data.get(SESSION)

    timezone: str = dialog_manager.start_data.get(TIME_ZONE)
    today: datetime = get_current_datetime(timezone)

    stmt = (
        select(Schedule)
        .where(
            Schedule.trainer_id == trainer_id,
            Schedule.client_id == client_id,
            Schedule.date >= today.date()
        )
    )

    result = await session.execute(stmt)

    return result.scalars().all()


async def get_trainers(
    dialog_manager: DialogManager,
) -> list[Trainer] | None:
    """
    Получает список объектов Trainer, связанных с текущим клиентом.
    """

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
