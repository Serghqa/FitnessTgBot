from .models import Trainer, Client, RelationUsers, Schedule, WorkingDay, TrainerSchedule, Workout, Base


def set_trainer(id: int, name: str) -> Trainer:

    return Trainer(id=id, name=name)


def set_client(id: int, name: str) -> Client:

    return Client(id=id, name=name)


def set_workout(trainer_id: int, workouts: int, client_id: int) -> Workout:

    return Workout(trainer_id=trainer_id, workouts=workouts, client_id=client_id)


def set_schedule(client_id: int, trainer_id: int, date: str, time: int) -> Schedule:

    return Schedule(client_id=client_id, trainer_id=trainer_id, date=date, time=time)


def set_work_day(item: int, work: str, trainer_id: int) -> WorkingDay:

    return WorkingDay(item=item, work=work, trainer_id=trainer_id)


def set_trainer_schedule(date: str, time: str, trainer_id: int) -> TrainerSchedule:

    return TrainerSchedule(date=date, time=time, trainer_id=trainer_id)


__all__ = [set_trainer, set_client, set_schedule, set_work_day, set_trainer_schedule, Base]
