"""Нормализация дат для фильтров."""
from datetime import datetime, time, timezone


def _as_utc_naive(dt: datetime) -> datetime:
    """Привести к naive UTC для сравнения с DATETIME в MySQL."""
    if dt.tzinfo is not None:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def normalize_range_start(from_date: datetime | None) -> datetime | None:
    """Дата без времени = начало дня (00:00:00)."""
    if from_date is None:
        return None
    if from_date.time() == time(0, 0, 0) and from_date.tzinfo is None:
        return from_date
    if from_date.time() == time(0, 0, 0):
        return _as_utc_naive(from_date)
    return _as_utc_naive(from_date)


def normalize_range_end(to_date: datetime | None) -> datetime | None:
    """Дата без времени = конец дня; ISO с временем — как есть."""
    if to_date is None:
        return None
    dt = _as_utc_naive(to_date)
    if to_date.time() == time(0, 0, 0) and to_date.tzinfo is None:
        return dt.replace(hour=23, minute=59, second=59, microsecond=999999)
    return dt
