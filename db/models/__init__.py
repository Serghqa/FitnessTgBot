from .models import Trainer, Client, Base


def set_trainer(
    user_id: int,
    name: str
) -> Trainer:

    return Trainer(
        trainer_id=user_id,
        name=name
    )


def set_client(
    user_id: int,
    name: str,
    trainer_id: int
) -> Client:
    
    return Client(
        client_id=user_id,
        name=name,
        trainer_id=trainer_id
    )


__all__ = [set_trainer, set_client, Base]
