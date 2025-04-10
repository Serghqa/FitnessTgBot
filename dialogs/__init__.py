from aiogram import Router
from dialogs import (
    start_dialog,
    validate_dialog,
    trainer_dialog,
    client_edit_dialog,
    client_dialog
)


def setup_all_dialogs(router: Router) -> Router:

    router = Router()

    start_dialog.setup(router)
    validate_dialog.setup(router)
    trainer_dialog.setup(router)
    client_edit_dialog.setup(router)
    client_dialog.setup(router)

    return router
