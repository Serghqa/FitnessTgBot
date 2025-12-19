import logging

from aiogram_dialog import DialogManager
from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo

from timezones import timezones


CLIENT = 'is_client'
NAME = 'name'
IS_CHECKED = 'is_checked'
RADIO = 'radio'
RADIO_GROUP = 'radio_group'
RADIO_TZ = 'radio_tz'
TIME_ZONE = 'time_zone'
TRAINER = 'is_trainer'
TRAINERS = 'trainers'
WORKOUTS = 'workouts'


logger = logging.getLogger(__name__)


def _radio_checked(dialog_manager: DialogManager, key: str) -> bool:
    """
    Проверяет, выбран ли какой-либо вариант в группе переключателей.

    Эта функция определяет, сделал ли пользователь выбор в группе
    переключателей, связанных с заданным ключом в данных виджета.

    Возвращает:
        bool: True, если выбор существует,
        False в противном случае.
    """

    widget_item: str | None = \
        dialog_manager.current_context().widget_data.get(key)
    return widget_item is not None


def format_current_time_with_tz(time_zone: str) -> str:
    """
    Форматировать текущее время в указанном часовом поясе как
    «Area/City HH:MM».
    """

    tz = ZoneInfo(time_zone)
    now = datetime.now(tz)

    return f'{time_zone} {now.strftime('%H:%M')}'


async def get_data(
    dialog_manager: DialogManager,
    **kwargs
) -> dict[str, bool]:

    calc_data = {
        TRAINER: TIME_ZONE in dialog_manager.start_data,
        CLIENT: WORKOUTS in dialog_manager.start_data
    }

    return calc_data


async def get_radio_data(
    dialog_manager: DialogManager,
    **kwargs
) -> dict[str, Any]:
    """
    Функция-получатель для диалогового окна, содержащего группу радиокнопок
    для тренеров.
    """

    is_checked: bool = _radio_checked(
        dialog_manager=dialog_manager,
        key=RADIO_GROUP,
    )

    trainers: list[dict] = dialog_manager.dialog_data[TRAINERS]

    return {
        IS_CHECKED: is_checked,
        RADIO: [(trainer[NAME], i) for i, trainer in enumerate(trainers)]
    }


async def get_timezones(
    dialog_manager: DialogManager,
    **kwargs
) -> dict[str, Any]:
    """
    Предоставляет данные диалога для отображения списка российских часовых
    поясов с текущим местным временем.

    Этот метод проверяет, выбран ли уже часовой пояс в
    группе переключателей, идентифицируемой `RADIO_TZ`, и подготавливает список
    отображаемых элементов для пользовательского интерфейса. Каждый элемент
    состоит из понятного человеку ярлыка
    (название часового пояса и текущее время) и самого названия часового пояса,
    используемого в качестве идентификатора элемента.
    """

    is_checked: bool = _radio_checked(
        dialog_manager=dialog_manager,
        key=RADIO_TZ,
    )

    return {
        IS_CHECKED: is_checked,
        RADIO_TZ: [
            (format_current_time_with_tz(tz), tz)
            for tz in timezones
        ]
    }
