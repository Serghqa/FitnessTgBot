import logging

from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import Context


logger = logging.getLogger(__name__)

EXIST = 'exist'
RADIO = 'radio'
RAD_SCHED = 'rad_sched'
ROWS = 'rows'
SEL_D = 'sel_d'
SELECTED_DATE = 'selected_date'
SELECTED_DATES = 'selected_dates'
SELECTED_TIME = 'selected_time'
WORKOUTS = 'workouts'


async def get_data_today(
    dialog_manager: DialogManager,
    **kwargs
) -> dict:
    """
    Функция получает тренировки клиента на сегодняшнюю дату и
    форматирует их для отображения в диалоге.
    """

    today: str = dialog_manager.dialog_data.get(SELECTED_DATE)
    schedule_times: list[int] = \
        dialog_manager.dialog_data[SELECTED_DATES][today]
    schedules_str = '\n'.join(f'• {t:02d}:00' for t in schedule_times)
    text = f'Мои тренировки:\n{schedules_str}'

    return {'today': today, 'text': text}


async def get_data_radio(
    dialog_manager: DialogManager,
    **kwargs
) -> dict:
    """
    Функция подготавливает данные для отображения.
    Преобразует список доступных времен в формат, пригодный для виджета.
    """

    selected_date: str = dialog_manager.dialog_data[SELECTED_DATE]
    times: list[int] = \
        dialog_manager.dialog_data[SELECTED_DATES][selected_date]
    data: list[tuple[int]] = [(t, item) for item, t in enumerate(times)]

    workouts: int = dialog_manager.start_data[WORKOUTS]

    return {RADIO: data, WORKOUTS: workouts}


async def get_exist_data(
    dialog_manager: DialogManager,
    **kwargs
) -> dict:
    """
    Подготавливает данные для отображения успешности записи
    на тренировку в окне диалога.
    """

    context: Context = dialog_manager.current_context()

    radio_item: int = int(context.widget_data.get(RAD_SCHED, 0))

    selected_date: str = dialog_manager.dialog_data[SELECTED_DATE]
    selected_time: int = \
        dialog_manager.dialog_data[SELECTED_DATES][selected_date][radio_item]

    return {
        SELECTED_DATE: selected_date,
        SELECTED_TIME: selected_time,
        EXIST: dialog_manager.dialog_data[EXIST]
    }


async def get_data_selected(
    dialog_manager: DialogManager,
    **kwargs
) -> dict:
    """
    Функция-геттер данных для получения и подготовки информации о выбранной
    дате и временах тренировок для отображения в диалоговом интерфейсе.
    """

    context: Context = dialog_manager.current_context()

    selected_date: str = dialog_manager.dialog_data[SELECTED_DATE]
    times: list[int] = sorted(
        dialog_manager.dialog_data[SELECTED_DATES].get(selected_date, [])
    )
    rows: list[tuple[int]] = [(i, t) for i, t in enumerate(times)]
    exist: bool = any(context.widget_data.get(SEL_D, []))

    return {
        SELECTED_DATE: selected_date,
        ROWS: rows,
        EXIST: exist
    }
