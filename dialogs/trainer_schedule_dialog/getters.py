import logging

from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities import Context
from aiogram_dialog.widgets.kbd.select import ManagedMultiselect
from typing import Any


logger = logging.getLogger(__name__)

CLIENT_NAME = 'client_name'
CLIENT_ID = 'client_id'
DATE = 'date'
IS_APPLY = 'is_apply'
IS_CANCEL = 'is_cancel'
RADIO = 'radio'
ROWS = 'rows'
SEL = 'sel'
SEL_D = 'sel_d'
SELECTED_DATES = 'selected_dates'
SELECTED_DATE = 'selected_date'
SCHEDULES = 'schedules'
TIME = 'time'
TRAININGS = 'trainings'


def format_schedule(work: str) -> str:
    """
    Форматирует строку с перечислением временных интервалов (часов) в
    строку диапазона.

    Принимает строку с числами, разделёнными запятыми (например, "11,13,15"),
    и возвращает строку в формате "минимум-максимум", например "11-15".
    """

    items = sorted(map(int, work.split(',')))

    return f'{items[0]}-{items[-1]}'


async def selection_getter(
    dialog_manager: DialogManager,
    **kwargs
) -> dict[str, Any]:
    """
    Асинхронная функция-получатель данных для отображения в окне диалога.

    Подготавливает контекстные данные для интерфейса выбора расписания:
    - Список расписаний с эмодзи-маркерами.
    - Индикатор, был ли уже применён какой-либо выбор.

    """

    data_radio: dict[str, list] = await get_data_radio(dialog_manager)

    is_apply: bool = any(
        item for item in dialog_manager.dialog_data[SELECTED_DATES].values()
        if isinstance(item, str)
    )

    return {
        RADIO: data_radio[RADIO],
        IS_APPLY: is_apply
    }


async def get_multiselect_data(
    dialog_manager: DialogManager,
    **kwargs
) -> dict[str, list[tuple[int, int, str]]]:
    """
    Подготавливает данные для отображения мультиселекта,
    где выбранные элементы помечаются эмодзи '🟢',
    чтобы показать рабочее время смены тренера.
    Невыбранные часы отображаются без метки.
    """

    widget: ManagedMultiselect = dialog_manager.find(SEL)

    items = {item: '🟢' for item in widget.get_checked()}

    return {
        ROWS: [(i, i, items.get(str(i), '')) for i in range(24)]
    }


async def get_data_radio(
    dialog_manager: DialogManager,
    **kwargs
) -> dict[str, list[tuple[str, str, str]]]:
    """
    Подготавливает данные для отображения радио-кнопок с
    расписанием и соответствующими эмодзи-метками.

    Каждый элемент расписания отображается с уникальной меткой (эмодзи),
    в зависимости от идентификатора, чтобы пользователь мог визуально
    различать разные варианты выбора в календаре.
    """

    marks = {'1': '🟢', '2': '🔵', '3': '🟣'}

    data: list[tuple[str, str, str]] = [
        (format_schedule(work), id, marks[id]) for id, work in
        dialog_manager.start_data[SCHEDULES].items()
    ]

    return {RADIO: data}


async def get_current_schedule(
    dialog_manager: DialogManager,
    **kwargs
) -> dict[str, Any]:
    """
    Подготавливает данные для отображения текущего
    расписания тренировок на день.
    """

    context: Context = dialog_manager.current_context()

    selected_date: str = \
        dialog_manager.dialog_data[SELECTED_DATE][DATE]
    trainings: list[dict] = \
        dialog_manager.dialog_data[SELECTED_DATE][TRAININGS]

    rows = [
        (i, data[CLIENT_NAME], data[TIME]) for i, data in enumerate(trainings)
    ]

    is_cancel: bool = any(context.widget_data.get(SEL_D, []))

    return {
        SELECTED_DATE: selected_date,
        ROWS: rows,
        IS_CANCEL: is_cancel
    }


async def today_getter(
    dialog_manager: DialogManager,
    **kwargs
) -> dict:
    """
    Функция форматирует данные о тренировках на выбранную
    дату для отображения тренеру. Извлекает информацию о
    клиентах и времени тренировок.
    """

    selected_date: str = \
        dialog_manager.dialog_data[SELECTED_DATE][DATE]
    trainings: list[dict] = \
        dialog_manager.dialog_data[SELECTED_DATE][TRAININGS]

    tmp = []

    for training in trainings:
        client_id: int = training[CLIENT_ID]
        client_name: str = training[CLIENT_NAME]
        time: int = training[TIME]

        message = \
            f'• client_id={client_id} client_name={client_name} {time:02d}:00'
        tmp.append(message)
    text = '\n'.join(tmp)

    data = {
        'today': selected_date,
        'text': text
    }
    return data
