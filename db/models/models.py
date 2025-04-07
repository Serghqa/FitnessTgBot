from sqlalchemy import BigInteger, String, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Trainer(Base):
    __tablename__ = 'trainer'

    trainer_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    group: Mapped[list['Client']] = relationship(back_populates='clients')

    def __repr__(self):
        return f'trainer_id={self.trainer_id}, name={self.name}'


class Client(Base):
    __tablename__ = 'client'

    client_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    trainer_id: Mapped[BigInteger] = mapped_column(BigInteger, ForeignKey('trainer.trainer_id'))
    clients: Mapped['Trainer'] = relationship(back_populates='group')

    def __repr__(self):
        return f'client_id={self.client_id}, name={self.name}'
