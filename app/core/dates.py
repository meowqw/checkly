"""Даты и часовые пояса: в БД — naive local time пользователя."""
from datetime import datetime, time
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

DEFAULT_TIMEZONE = "Europe/Moscow"


def resolve_timezone(name: str | None) -> str:
    candidate = (name or DEFAULT_TIMEZONE).strip()
    try:
        ZoneInfo(candidate)
        return candidate
    except ZoneInfoNotFoundError:
        return DEFAULT_TIMEZONE


def to_storage_datetime(dt: datetime, tz_name: str) -> datetime:
    """Сохранить в БД как naive local time в TZ пользователя."""
    tz = ZoneInfo(resolve_timezone(tz_name))
    if dt.tzinfo is not None:
        return dt.astimezone(tz).replace(tzinfo=None)
    return dt


def now_local(tz_name: str) -> datetime:
    return datetime.now(ZoneInfo(resolve_timezone(tz_name))).replace(tzinfo=None)


def normalize_range_start(from_date: datetime | None, tz_name: str = DEFAULT_TIMEZONE) -> datetime | None:
    """Граница from: начало календарного дня в TZ пользователя."""
    if from_date is None:
        return None

    tz = ZoneInfo(resolve_timezone(tz_name))
    if from_date.tzinfo is not None:
        local = from_date.astimezone(tz).replace(tzinfo=None)
        if from_date.time() == time(0, 0, 0):
            return datetime.combine(local.date(), time.min)
        return local

    if from_date.time() == time(0, 0, 0):
        return datetime.combine(from_date.date(), time.min)
    return from_date


def normalize_range_end(to_date: datetime | None, tz_name: str = DEFAULT_TIMEZONE) -> datetime | None:
    """Граница to: конец календарного дня в TZ пользователя."""
    if to_date is None:
        return None

    tz = ZoneInfo(resolve_timezone(tz_name))
    if to_date.tzinfo is not None:
        local = to_date.astimezone(tz).replace(tzinfo=None)
        if to_date.time() == time(0, 0, 0):
            return datetime.combine(local.date(), time(23, 59, 59, 999999))
        return local

    if to_date.time() == time(0, 0, 0):
        return to_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    return to_date
