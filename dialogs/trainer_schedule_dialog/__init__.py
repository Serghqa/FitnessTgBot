from aiogram import Router
from .dialog import trainer_schedule_dialog


def setup(router: Router):
    router.include_router(trainer_schedule_dialog)
