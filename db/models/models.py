from sqlalchemy import Integer, BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from typing import Any


class Base(DeclarativeBase):

    pass


class Trainer(Base):

    __tablename__ = 'trainer'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String)

    trainings: Mapped[list['Schedule']] = \
        relationship('Schedule', back_populates='trainer', lazy='joined')
    working_days: Mapped[list['WorkingDay']] = \
        relationship('WorkingDay', back_populates='trainer', lazy='joined')
    schedules: Mapped[list['TrainerSchedule']] = \
        relationship('TrainerSchedule', back_populates='trainer', lazy='joined')

    def __repr__(self):
        return f'id={self.id}, name={self.name}'

    def get_data(self) -> dict[str, Any]:
        return {
            'trainer': True,
            'id': self.id,
            'name': self.name
        }


class Client(Base):

    __tablename__ = 'client'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    workouts: Mapped[int] = mapped_column(Integer, default=0)
    trainer_id: Mapped[int] = mapped_column(BigInteger)

    trainings: Mapped[list['Schedule']] = \
        relationship('Schedule', back_populates='client', lazy='joined')

    def __repr__(self):

        return f'id={self.id}, name={self.name}'

    def get_data(self) -> dict[str, Any]:

        return {
            'id': self.id,
            'name': self.name,
            'workouts': self.workouts,
            'trainer_id': self.trainer_id
        }


class Schedule(Base):

    __tablename__ = 'schedule'

    id: Mapped[int] = \
        mapped_column(Integer, primary_key=True, autoincrement=True)
    client_id: Mapped[int] = \
        mapped_column(BigInteger, ForeignKey('client.id'))
    trainer_id: Mapped[int] = \
        mapped_column(BigInteger, ForeignKey('trainer.id'))
    date: Mapped[str] = mapped_column(String)
    time: Mapped[int] = mapped_column(Integer)

    client = relationship('Client', back_populates='trainings', lazy='joined')
    trainer = relationship('Trainer', back_populates='trainings', lazy='joined')

    def __repr__(self):

        return f'Training trainer_id={self.trainer_id}, '\
            f'client_id={self.client_id}'
    
    def get_data(self) -> dict[str, Any]:

        return {
            'client_id': self.client_id,
            'trainer_id': self.trainer_id,
            'date': self.date,
            'time': self.time
        }


class WorkingDay(Base):

    __tablename__ = 'working_day'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item: Mapped[int] = mapped_column(Integer)
    work: Mapped[str] = mapped_column(String)
    trainer_id: Mapped[int] =\
        mapped_column(BigInteger, ForeignKey('trainer.id'))

    trainer = relationship(
        'Trainer',
        back_populates='working_days',
        lazy='selectin'
    )

    def __repr__(self):

        return f'Work hours: {self.work}'

    def get_data(self):

        return {
            'id': self.id,
            'work': self.work
        }


class TrainerSchedule(Base):

    __tablename__ = 'trainer_schedule'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String)
    time: Mapped[str] = mapped_column(String)
    trainer_id: Mapped[int] =\
        mapped_column(BigInteger, ForeignKey('trainer.id'))

    trainer = relationship(
        'Trainer',
        back_populates='schedules',
        lazy='selectin'
    )

    def __repr__(self):

        return f'Date: {self.date}'

    def get_data(self):

        return {
            'date': self.date,
            'time': self.time
        }
