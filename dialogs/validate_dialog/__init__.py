from aiogram import Router
from .dialog import validate_dialog


def setup(router: Router):

    router.include_router(validate_dialog)
