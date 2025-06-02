from aiogram.fsm.state import StatesGroup, State


class ClientState(StatesGroup):
    main = State()
    message = State()
    schedule = State()
