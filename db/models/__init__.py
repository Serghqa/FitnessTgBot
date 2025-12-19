from datetime import date

from .models import (
    Base,
    Client,
    RelationUsers,
    Schedule,
    Trainer,
    TrainerSchedule,
    WorkingDay,
    Workout,
)


def set_trainer(
    id: int,
    name: str,
    time_zone: str
) -> Trainer:

    return Trainer(
        id=id,
        name=name,
        time_zone=time_zone,
    )


def set_client(
    id: int,
    name: str
) -> Client:

    return Client(
        id=id,
        name=name,
    )


def set_workout(
    trainer_id: int,
    workouts: int,
    client_id: int
) -> Workout:

    return Workout(
        trainer_id=trainer_id,
        workouts=workouts,
        client_id=client_id,
    )


def set_schedule(
    client_id: int,
    trainer_id: int,
    date: date,
    time: int
) -> Schedule:

    return Schedule(
        client_id=client_id,
        trainer_id=trainer_id,
        date=date,
        time=time,
    )


def set_work_day(
    item: str,
    work: str,
    trainer_id: int
) -> WorkingDay:

    return WorkingDay(
        item=item,
        work=work,
        trainer_id=trainer_id,
    )


def set_trainer_schedule(
    date: date,
    time: str,
    trainer_id: int
) -> TrainerSchedule:

    return TrainerSchedule(
        date=date,
        time=time,
        trainer_id=trainer_id,
    )


def set_relation_users(
    trainer_id: int,
    client_id: int
) -> RelationUsers:

    return RelationUsers(
        trainer_id=trainer_id,
        client_id=client_id,
    )


__all__ = [
    Base,
    Client,
    RelationUsers,
    Schedule,
    Trainer,
    TrainerSchedule,
    WorkingDay,
    Workout,
    set_client,
    set_relation_users,
    set_schedule,
    set_trainer,
    set_trainer_schedule,
    set_work_day,
]
