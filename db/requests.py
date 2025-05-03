from aiogram_dialog import DialogManager

from sqlalchemy.orm import Session
from sqlalchemy import select

from faker import Faker

from db.models import set_trainer, set_client, set_daily_schedule, Trainer, Client, DailySchedule
from typing import Any


def get_user(
    session: Session,
    user_id: int,
    model: Client | Trainer
) -> Trainer | Client:

    user = session.get(model, user_id)

    return user


def add_trainer(dialog_manager: DialogManager):

    session: Session = dialog_manager.middleware_data.get('session')

    id = dialog_manager.event.from_user.id
    name = dialog_manager.event.from_user.id or 'no_name'

    user: Trainer = set_trainer(id=id, name=name)
    daily_schedule_1: DailySchedule = _add_daily_schedule(session, user, 1, 9, 9, '1')
    daily_schedule_2: DailySchedule = _add_daily_schedule(session, user, 2, 8, 12, '2')
    daily_schedule_3: DailySchedule = _add_daily_schedule(session, user, 3, 10, 12, '2')

    session.add_all([user, daily_schedule_1, daily_schedule_2, daily_schedule_3])
    session.commit()


def add_client(dialog_manager: DialogManager, trainer_id: int):

    session: Session = dialog_manager.middleware_data.get('session')

    fake = Faker(locale='ru_RU')

    for i in range(100_000_000, 100_001_000):  # удалить
        user: Client = set_client(i, fake.name(), trainer_id)  # удалить
        session.add(user)  # удалить

    session.commit()  # удалить


def update_workouts(dialog_manager: DialogManager) -> None:

    client_id = dialog_manager.start_data['id']
    value = dialog_manager.start_data['workout'] + dialog_manager.start_data['workouts']

    if value < 0:
        value = 0

    session: Session = dialog_manager.middleware_data.get('session')

    dialog_manager.start_data['workouts'] = value
    dialog_manager.start_data['workout'] = 0

    stmt = select(Client).filter(client_id == Client.id)
    res = session.execute(stmt)
    client = res.scalar()
    client.workouts = value

    session.commit()


def get_data_user(
    dialog_manager: DialogManager,
    model: Client | Trainer,
    id: int | None = None
) -> dict[str, Any]:

    session: Session = dialog_manager.middleware_data.get('session')
    id = id or dialog_manager.event.from_user.id

    data = {
        'client': None,
        'trainer': None,
        'id': None,
        'name': None,
        'workouts': None,
        'trainer_id': None,
        'radio_default': '1'
    }

    user = get_user(session, id, model)

    if user:
        data.update(user.get_data())

    return data


def get_group(dialog_manager: DialogManager) -> list[dict]:

    offset = dialog_manager.dialog_data.get('offset')
    limit = dialog_manager.dialog_data.get('limit')
    id = dialog_manager.event.from_user.id

    session: Session = dialog_manager.middleware_data.get('session')

    smtm = select(Client).filter(Client.trainer_id == id).order_by(Client.id).offset(offset).limit(limit)
    group = [row.Client.get_data() for row in session.execute(smtm).all()]

    return group


def _add_daily_schedule(
        session: Session,
        trainer: Trainer,
        id: int,
        start_work: int,
        working_hours: int,
        lunch_breaks: str
) -> DailySchedule:

    daily_schedule: DailySchedule = set_daily_schedule(
        trainer=trainer,
        id=id,
        start_work=start_work,
        working_hours=working_hours,
        lunch_breaks=lunch_breaks
    )

    return daily_schedule


def get_daily_schedules(dialog_manager: DialogManager) -> list[dict]:

    id = dialog_manager.event.from_user.id

    session: Session = dialog_manager.middleware_data.get('session')

    user: Trainer = get_user(session, id, Trainer)
