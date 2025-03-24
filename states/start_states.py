from aiogram.fsm.state import StatesGroup, State


class StartSG(StatesGroup):
    start = State()
    trainer_validate = State()
    client_validate = State()
