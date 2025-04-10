from aiogram import Router
from .dialog import client_edit_dialog


def setup(router: Router):
    router.include_router(client_edit_dialog)
