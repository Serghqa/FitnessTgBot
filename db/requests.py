from aiogram_dialog import DialogManager
from db.models import set_trainer, set_client, Trainer, Client
from sqlalchemy.orm import Session
from sqlalchemy import select
from typing import Any


def add_trainer_db(
    session: Session,
    user_id: int,
    name: str,
) -> None:

    user: Trainer = set_trainer(user_id, name)

    session.add(user)
    session.commit()


def add_client_db(
    session: Session,
    user_id: int,
    name: str,
    trainer_id: int
) -> None:

    user: Client = set_client(user_id, name, trainer_id)

    session.add(user)
    session.commit()


def update_data_client(
    session: Session,
    client_id: int,
    value: int
) -> None:
    
    stmt = select(Client).where(client_id == Client.client_id)
    res = session.execute(stmt)
    client = res.scalar()
    client.workouts = value

    session.commit()
    

def get_user(
    session: Session,
    user_id: int,
    user: Client | Trainer
) -> Trainer | Client:
    
    user = session.get(user, user_id)

    return user


def get_data_user(
    session: Session,
    user_id: int,
    model: Client | Trainer = Client,
    group = False
) -> dict[str, Any]:
    
    data = {
        'client': None,
        'trainer': None,
        'id': None,
        'name': None,
        'group': None,
        'workouts': None,
        'trainer_id': None
    }

    if issubclass(model, Client):
        user = get_user(session, user_id, model)

    if issubclass(model, Trainer):
        user = get_user(session, user_id, model)
        
    if user:
        data.update(user.get_data())
        if group:
            data['group'] = user.get_group()

    return data
