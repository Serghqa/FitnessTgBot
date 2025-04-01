from aiogram import Router
from .dialog import start_dialog


def setup(router: Router):
    router.include_router(start_dialog)
