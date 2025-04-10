from aiogram import Router
from .dialog import trainer_dialog


def setup(router: Router):
    router.include_router(trainer_dialog)
