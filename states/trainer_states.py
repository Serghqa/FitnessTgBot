from aiogram.fsm.state import StatesGroup, State


class TrainerState(StatesGroup):
    main = State()
    group = State()
