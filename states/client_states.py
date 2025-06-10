from aiogram.fsm.state import StatesGroup, State


class ClientState(StatesGroup):
    main = State()
    message = State()
    schedule = State()
    sign_training = State()
    sign_up = State()
