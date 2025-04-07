from .models import Trainer, Client, Base


def set_user(
    user_id: int,
    name: str,
    trainer_id: int = None
) -> Trainer | Client:
    
    if trainer_id:
        return Client(
            client_id = user_id, 
            name = name,
            trainer_id = trainer_id
        )
    return Trainer(
        trainer_id = user_id,
        name = name
    )
