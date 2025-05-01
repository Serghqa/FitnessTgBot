from aiogram.fsm.state import StatesGroup, State


class StartSG(StatesGroup):
    main = State()
    trainer = State()
    client = State()
