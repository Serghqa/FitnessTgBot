from aiogram.fsm.state import StatesGroup, State


class ClientEditState(StatesGroup):
    main = State()
    workout_edit = State()
