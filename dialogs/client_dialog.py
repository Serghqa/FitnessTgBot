import logging

from aiogram_dialog import Dialog, Window
from aiogram_dialog.widgets.text import Format
from states import ClientState

logger = logging.getLogger(__name__)


client_dialog = Dialog(
    Window(
        Format(
            text='Главное окно клиента',
        ),
        state=ClientState.main
    ),
)
