from aiogram import Router
from .dialog import tariner_dialog


def setup(router: Router):
    router.include_router(tariner_dialog)
