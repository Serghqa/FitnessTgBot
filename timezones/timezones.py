from datetime import datetime
from zoneinfo import ZoneInfo


timezones = (
    'Europe/Kaliningrad',
    'Europe/Moscow',
    'Europe/Samara',
    'Asia/Yekaterinburg',
    'Asia/Omsk',
    'Asia/Novosibirsk',
    'Asia/Irkutsk',
    'Asia/Yakutsk',
    'Asia/Vladivostok',
    'Asia/Magadan',
    'Asia/Kamchatka',
)


def get_current_datetime(timezone: str) -> datetime:
    """
    Возвращает текущую дату и время в указанном часовом поясе.
    """

    tz = ZoneInfo(timezone)
    return datetime.now(tz)
