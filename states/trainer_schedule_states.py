from aiogram.fsm.state import StatesGroup, State


class TrainerScheduleStates(StatesGroup):
    main = State()
    create_schedule = State()
    custom_create_schedule = State()
