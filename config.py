from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    TOKEN: str
    IS_TRAINER: str


@dataclass
class DbConfig:
    NAME: str
    PASSWORD: str
    HOST: str


@dataclass
class NatsConfig:
    servers: list[str]


@dataclass
class NatsConsumerConfig:
    subject_name: str
    stream_name: str
    durable_name: str


@dataclass
class Config:
    tg_bot: TgBot
    data_base: DbConfig
    nats: NatsConfig
    nats_consumer: NatsConsumerConfig


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        tg_bot=TgBot(
            env('TOKEN'),
            env('IS_TRAINER'),
        ),
        data_base=DbConfig(
            env('NAME'),
            env('PASSWORD'),
            env('HOST'),
        ),
        nats=NatsConfig(servers=env.list('NATS_SERVERS')),
        nats_consumer=NatsConsumerConfig(
            subject_name=env('NATS_SUBJECT_NAME'),
            stream_name=env('NATS_STREAM_NAME'),
            durable_name=env('NATS_DURABLE_NAME'),
        ),
    )
