from aiogram_dialog import DialogManager
from db.models import set_user, Trainer, Client
from sqlalchemy.orm import Session


def add_user_db(
    session: Session,
    user_id: int,
    name: str,
    trainer_id: int = None
) -> None:

    user: Trainer | Client = set_user(user_id, name, trainer_id)
    user = set_user(user_id, name, trainer_id)

    session.add(user)
    session.commit()


def get_data_user(
    session: Session,
    dialog_manager: DialogManager,
    group=False
) -> dict[str, str | int]:

    trainer, client, user_name = None, None, None
    user_id = dialog_manager.event.from_user.id

    client = session.get(Client, user_id)
    if not client:
        trainer = session.get(Trainer, user_id)
        if trainer and group:
            group = [
                {
                    'client_id': user.client_id,
                    'name': user.name,
                    'workouts': user.workouts
                 }
                for user in trainer.group
            ]

    if client:
        user_name = client.name
    elif trainer:
        user_name = trainer.name

    data = {
        'user': not trainer and not client,
        'client': client,
        'trainer': trainer,
        'id': user_id,
        'name': user_name,
        'group': group
    }
    return data
