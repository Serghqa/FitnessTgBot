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
    name = dialog_manager.event.from_user.full_name

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


def update_workouts_client(dialog_manager: DialogManager) -> None:

    client_id = dialog_manager.start_data['id']
    value = dialog_manager.start_data['workout'] + dialog_manager.start_data['workouts']
    if value < 0:
        value = 0

    session: Session = dialog_manager.middleware_data['session']

    dialog_manager.start_data['workouts'] = value
    dialog_manager.start_data['workout'] = 0

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
    dialog_manager: DialogManager,
    model: Client | Trainer = Client,
    group=False
) -> dict[str, Any]:

    session: Session = dialog_manager.middleware_data.get('session')
    user_id = dialog_manager.event.from_user.id

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
