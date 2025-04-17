from sqlalchemy import Integer, BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from typing import Any


class Base(DeclarativeBase):

    pass


class Trainer(Base):

    __tablename__ = 'trainer'

    trainer_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    group: Mapped[list['Client']] = relationship(back_populates='clients')


    def __repr__(self):

        return f'trainer_id={self.trainer_id}, name={self.name}'
    

    def get_data(self) -> dict[str, Any]:
        
        return {
            'trainer': True,
            'id': self.trainer_id,
            'name': self.name
        }
    

    def get_group(self) -> list[dict[str, Any]]:

        return [user.get_data() for user in self.group]


class Client(Base):

    __tablename__ = 'client'

    client_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    workouts: Mapped[int] = mapped_column(Integer, default=0)
    trainer_id: Mapped[BigInteger] = mapped_column(BigInteger, ForeignKey('trainer.trainer_id'))
    clients: Mapped['Trainer'] = relationship(back_populates='group')


    def __repr__(self):

        return f'client_id={self.client_id}, name={self.name}'
    

    def get_data(self):

        return {
            'client': True,
            'id': self.client_id,
            'name': self.name,
            'workouts': self.workouts,
            'trainer_id': self.trainer_id
        }
