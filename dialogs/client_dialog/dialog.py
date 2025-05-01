import logging

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Const

from states import ClientState


logger = logging.getLogger(__name__)


client_dialog = Dialog(
    Window(
        Const(
            text='Главное окно клиента',
        ),
        state=ClientState.main
    ),
)
