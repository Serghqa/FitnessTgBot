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
class Config:
    tg_bot: TgBot
    data_base: DbConfig


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
    )
