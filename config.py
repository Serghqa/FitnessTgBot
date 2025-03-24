from dataclasses import dataclass
from environs import Env


@dataclass
class TgBot:
    TOKEN: str
    IS_TRAINER: str


@dataclass
class Config:
    tg_bot: TgBot


def load_config(path: str | None = None) -> Config:
    env = Env()
    env.read_env(path)
    return Config(
        tg_bot=TgBot(
            env('TOKEN'),
            env('IS_TRAINER')
        )
    )
