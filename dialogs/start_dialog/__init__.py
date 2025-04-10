from aiogram import Router
from .dialog import start_router


def setup(router: Router):

    router.include_router(start_router)
