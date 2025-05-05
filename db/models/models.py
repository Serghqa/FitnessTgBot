from sqlalchemy import Integer, BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

from typing import Any


class Base(DeclarativeBase):

    pass


class Trainer(Base):

    __tablename__ = 'trainer'

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String)

    trainings = relationship('Schedule', back_populates='trainer')
    daily_schedules: Mapped[list['DailySchedule']] = \
        relationship('DailySchedule', back_populates='trainer', lazy='joined')

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

    trainings = relationship('Schedule', back_populates='client')

    def __repr__(self):

        return f'id={self.id}, name={self.name}'

    def get_data(self) -> dict[str, Any]:

        return {
            'client': True,
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

    client = relationship('Client', back_populates='trainings')
    trainer = relationship('Trainer', back_populates='trainings')

    def __repr__(self):

        return f'Training trainer_id={self.trainer_id}, '\
            f'client_id={self.client_id}'


class DailySchedule(Base):

    __tablename__ = 'daily_schedule'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    start_work: Mapped[int] = mapped_column(Integer)
    working_hours: Mapped[int] = mapped_column(Integer)
    lunch_breaks: Mapped[str] = mapped_column(String)

    trainer_id: Mapped[int] =\
        mapped_column(BigInteger, ForeignKey('trainer.id'))
    trainer = relationship(
        'Trainer',
        back_populates='daily_schedules',
        lazy='selectin'
    )

    def __repr__(self):

        return f'Start of the workingvday: {self.start_work}, '\
            f'end of the working day: {self.start_work + self.working_hours}'

    def get_data(self):

        return {
            'start_work': self.start_work,
            'working_hours': self.working_hours,
            'launch_breaks': [
                int(lunch) for lunch in self.lunch_breaks.split(', ')
            ]
        }
