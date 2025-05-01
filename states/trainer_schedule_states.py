from aiogram.fsm.state import StatesGroup, State


class TrainerScheduleStates(StatesGroup):
    main = State()
    schedule = State()
    work = State()

