from aiogram.fsm.state import State, StatesGroup


class TrainerScheduleStates(StatesGroup):
    confirmation = State()
    edit_work = State()
    main = State()
    selected_date = State()
    schedule = State()
    work = State()
