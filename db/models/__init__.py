from .models import Trainer, Client, Schedule, Base


def set_trainer(id: int, name: str) -> Trainer:

    return Trainer(id=id, name=name)


def set_client(id: int, name: str, trainer_id: int) -> Client:

    return Client(id=id, name=name, trainer_id=trainer_id)


def set_schedule(client_id: int, trainer_id: int):

    return Schedule(client_id=client_id, trainer_id=trainer_id)


__all__ = [set_trainer, set_client, set_schedule, Base]
