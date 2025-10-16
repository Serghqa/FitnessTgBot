from datetime import date as dt

from sqlalchemy import BigInteger, Date, ForeignKey, Integer,  String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from typing import Any


class Base(DeclarativeBase):

    pass


class Trainer(Base):

    __tablename__ = 'trainer'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True,)
    name: Mapped[str] = mapped_column(String)
    time_zone: Mapped[str] = mapped_column(String)

    clients: Mapped[list['Client']] = relationship(
        back_populates='trainers',
        secondary='relation_users',
        uselist=True,
        order_by='Client.id',
    )
    schedules: Mapped[list['Schedule']] = relationship(
        'Schedule',
        back_populates='trainer',
    )
    working_days: Mapped[list['WorkingDay']] = relationship(
        'WorkingDay',
        back_populates='trainer',
        order_by='WorkingDay.item',
    )
    trainer_schedules: Mapped[list['TrainerSchedule']] = relationship(
        'TrainerSchedule',
        back_populates='trainer',
        order_by='TrainerSchedule.date',
    )

    def get_data(self) -> dict[str, Any]:

        return {
            'id': self.id,
            'name': self.name,
            'time_zone': self.time_zone,
        }


class Client(Base):

    __tablename__ = 'client'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True,)
    name: Mapped[str] = mapped_column(String)

    trainers: Mapped[list['Trainer']] = relationship(
        back_populates='clients',
        secondary='relation_users',
        uselist=True,
        order_by='Trainer.id',
    )
    workouts: Mapped[list['Workout']] = relationship(
        'Workout',
        back_populates='client',
    )
    schedules: Mapped[list['Schedule']] = relationship(
        'Schedule',
        back_populates='client',
    )

    def get_data(self) -> dict[str, Any]:

        return {
            'id': self.id,
            'name': self.name,
        }


class RelationUsers(Base):

    __tablename__ = 'relation_users'

    trainer_id: Mapped[int] = mapped_column(
        ForeignKey('trainer.id'),
        primary_key=True,
    )
    client_id: Mapped[int] = mapped_column(
        ForeignKey('client.id'),
        primary_key=True,
    )


class Workout(Base):

    __tablename__ = 'workout'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    trainer_id: Mapped[int] = mapped_column(BigInteger)
    workouts: Mapped[int] = mapped_column(Integer, default=0,)
    client_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('client.id'),
    )

    client: Mapped['Client'] = relationship(
        'Client',
        back_populates='workouts',
    )

    def get_data(self) -> dict[str, int]:

        return {
            'workouts': self.workouts
        }


class Schedule(Base):

    __tablename__ = 'schedule'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    client_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('client.id'),
    )
    trainer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('trainer.id'),
    )
    date: Mapped[dt] = mapped_column(Date)
    time: Mapped[int] = mapped_column(Integer)

    client = relationship('Client', back_populates='schedules',)
    trainer = relationship('Trainer', back_populates='schedules',)

    def get_data(self) -> dict[str, Any]:

        return {
            'client_id': self.client_id,
            'trainer_id': self.trainer_id,
            'date': self.date,
            'time': self.time,
        }


class WorkingDay(Base):

    __tablename__ = 'working_day'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    item: Mapped[str] = mapped_column(String)
    work: Mapped[str] = mapped_column(String)
    trainer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('trainer.id'),
    )

    trainer: Mapped['Trainer'] = relationship(
        'Trainer',
        back_populates='working_days',
    )

    def get_data(self):

        return {
            'item': self.item,
            'work': self.work,
        }


class TrainerSchedule(Base):

    __tablename__ = 'trainer_schedule'

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )
    date: Mapped[dt] = mapped_column(Date)
    time: Mapped[str] = mapped_column(String)
    trainer_id: Mapped[int] = mapped_column(
        BigInteger,
        ForeignKey('trainer.id'),
    )

    trainer = relationship(
        'Trainer',
        back_populates='trainer_schedules',
    )

    def get_data(self):

        return {
            'date': self.date,
            'time': self.time,
        }
