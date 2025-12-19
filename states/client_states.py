from aiogram.fsm.state import State, StatesGroup


class ClientState(StatesGroup):
    cancel_training = State()
    today = State()
    main = State()
    my_sign_up = State()
    schedule = State()
    sign_training = State()
    sign_up = State()
