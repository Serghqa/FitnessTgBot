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


def get_time_zones() -> list[str]:
    return [tz for tz in timezones]


def get_current_date(timezone: str) -> datetime:
    tz = ZoneInfo(timezone)
    return datetime.now(tz)
