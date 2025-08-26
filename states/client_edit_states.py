from aiogram.fsm.state import State, StatesGroup


class ClientEditState(StatesGroup):
    main = State()
    workout_edit = State()
