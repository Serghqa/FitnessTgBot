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


def get_trainer(
    session: Session,
    user_id: int,
    group: int = None
) -> dict:
    
    user = session.get(Trainer, user_id)
    if not user:
        return

    data = {'id': user.trainer_id, 'name': user.name}
    if group:
        clients = [{'client_id': client.client_id, 'name': client.name} for client in user.group]
        data['group'] = clients
    return data


def get_client(
    session: Session,
    user_id: int
) -> dict:
    
    user = session.get(Client, user_id)
    if not user:
        return
    
    data = {'id': user.client_id, 'name': user.name}
    return data
    