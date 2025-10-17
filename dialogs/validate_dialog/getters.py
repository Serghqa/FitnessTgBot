import logging

from aiogram_dialog import DialogManager
from aiogram_dialog.api.entities.context import Context

from datetime import datetime

from zoneinfo import ZoneInfo

from timezones import get_time_zones


NAME = 'name'
IS_CHECKED = 'is_checked'
RADIO = 'radio'
RADIO_GROUP = 'radio_group'
RADIO_TZ = 'radio_tz'
TRAINERS = 'trainers'


logger = logging.getLogger(__name__)


def _radio_checked(dialog_manager: DialogManager, key: str) -> bool:

    context: Context = dialog_manager.current_context()

    is_checked: str | None = context.widget_data.get(key)

    return is_checked is not None


def _strftime(time_zone: str) -> str:

    tz: ZoneInfo = ZoneInfo(time_zone)
    t = datetime.now(tz).time().strftime('%H:%M')

    return f'{tz.key} {t}'


async def get_data(dialog_manager: DialogManager, **kwargs):

    return dialog_manager.start_data


async def get_radio_data(dialog_manager: DialogManager, **kwargs):

    is_checked: bool = _radio_checked(
        dialog_manager=dialog_manager,
        key=RADIO_GROUP,
    )

    trainers: list[dict] = dialog_manager.dialog_data[TRAINERS]

    return {
        IS_CHECKED: is_checked,
        RADIO: [(trainer[NAME], i) for i, trainer in enumerate(trainers)]
    }


async def get_timezones(dialog_manager: DialogManager, **kwargs):

    timezones: list[str] = get_time_zones()

    is_checked: bool = _radio_checked(
        dialog_manager=dialog_manager,
        key=RADIO_TZ,
    )

    return {
        IS_CHECKED: is_checked,
        RADIO_TZ: [(_strftime(tz), i) for i, tz in enumerate(timezones)]
    }
