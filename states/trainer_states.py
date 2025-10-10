from aiogram.fsm.state import State, StatesGroup


class TrainerState(StatesGroup):
    client = State()
    group = State()
    main = State()
