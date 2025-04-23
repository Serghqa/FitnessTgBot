from aiogram_dialog import DialogManager
from sqlalchemy.orm import Session
from sqlalchemy import select
from db.models import set_trainer, set_client, Trainer, Client
from typing import Any


def add_user(
    dialog_manager: DialogManager,
    trainer_id=None
) -> None:
    
    session: Session = dialog_manager.middleware_data.get('session')

    user_id = dialog_manager.event.from_user.id
    name = dialog_manager.event.from_user.full_name or 'no_name'

    if trainer_id is None:
        user: Trainer = set_trainer(user_id, name)

    else:
        #  Для отладки
        ids = [123456780, 123654789, 456789123, 159753654, 456369852, 456369855]  # удалить
        names = ['sedhh', 'hgvghd', 'hjgtd', 'ghfgcxfdxf', 'ghcfgxdf', 'fvccszsd']  # удалить
        for i in range(len(ids)):  # удалить
            user: Client = set_client(ids[i], names[i], trainer_id)  # удалить
            session.add(user)  # удалить
        session.commit()  # удалить
        return  # удалить
        #  user: Client = set_client(user_id, name, trainer_id) разкомментировать

    session.add(user)
    session.commit()


def update_workouts(dialog_manager: DialogManager) -> None:

    client_id = dialog_manager.start_data['id']
    value = dialog_manager.start_data['workout'] + dialog_manager.start_data['workouts']

    if value < 0:
        value = 0

    session: Session = dialog_manager.middleware_data['session']

    dialog_manager.start_data['workouts'] = value
    dialog_manager.start_data['workout'] = 0

    stmt = select(Client).where(client_id == Client.id)
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
    dialog_manager: DialogManager,
    model: Client | Trainer,
    user_id: int | None = None
) -> dict[str, Any]:
    
    session: Session = dialog_manager.middleware_data.get('session')
    user_id = user_id or dialog_manager.event.from_user.id

    data = {
        'client': None,
        'trainer': None,
        'id': None,
        'name': None,
        'workouts': None,
        'trainer_id': None,
        'radio_default': '1'
    }

    user = get_user(session, user_id, model)

    if user:
        data.update(user.get_data())

    return data


def get_group(dialog_manager: DialogManager) -> list[dict]:

    offset = dialog_manager.dialog_data.get('offset')
    limit = dialog_manager.dialog_data.get('limit')
    
    session: Session = dialog_manager.middleware_data.get('session')

    smtm = select(Client).order_by(Client.id).offset(offset).limit(limit)
    group = [row.Client.get_data() for row in session.execute(smtm).all()]
    
    return group
