from .models import Trainer, Client, Schedule, WorkingDay, TrainerSchedule, Base


def set_trainer(id: int, name: str) -> Trainer:

    return Trainer(id=id, name=name)


def set_client(id: int, name: str, trainer_id: int) -> Client:

    return Client(id=id, name=name, trainer_id=trainer_id)


def set_schedule(client_id: int, trainer_id: int) -> Schedule:

    return Schedule(client_id=client_id, trainer_id=trainer_id)


def set_work_day(trainer: Trainer, id: int, work: str) -> WorkingDay:

    return WorkingDay(trainer=trainer, id=id, work=work)


def set_trainer_schedule(date: str, time: str, trainer_id: int) -> TrainerSchedule:

    return TrainerSchedule(date=date, time=time, trainer_id=trainer_id)


__all__ = [set_trainer, set_client, set_schedule, set_work_day, set_trainer_schedule, Base]
