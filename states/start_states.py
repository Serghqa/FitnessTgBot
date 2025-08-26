from aiogram.fsm.state import State, StatesGroup


class StartSG(StatesGroup):
    client = State()
    group = State()
    main = State()
    trainer = State()
