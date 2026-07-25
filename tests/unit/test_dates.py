"""Unit: dates / timezone helpers."""
from datetime import datetime, timezone

from app.core.dates import (
    DEFAULT_TIMEZONE,
    normalize_range_end,
    normalize_range_start,
    resolve_timezone,
    to_storage_datetime,
)


def test_resolve_timezone_valid() -> None:
    assert resolve_timezone("Asia/Tomsk") == "Asia/Tomsk"


def test_resolve_timezone_invalid_falls_back() -> None:
    assert resolve_timezone("Not/AZone") == DEFAULT_TIMEZONE
    assert resolve_timezone(None) == DEFAULT_TIMEZONE
    assert resolve_timezone("  ") == DEFAULT_TIMEZONE


def test_to_storage_datetime_naive_passthrough() -> None:
    dt = datetime(2026, 6, 15, 14, 30, 0)
    assert to_storage_datetime(dt, "Europe/Moscow") == dt


def test_to_storage_datetime_aware_to_local_naive() -> None:
    # 12:00 UTC = 15:00 Moscow (UTC+3)
    aware = datetime(2026, 6, 15, 12, 0, 0, tzinfo=timezone.utc)
    stored = to_storage_datetime(aware, "Europe/Moscow")
    assert stored.tzinfo is None
    assert stored == datetime(2026, 6, 15, 15, 0, 0)


def test_normalize_range_start_date_only() -> None:
    day = datetime(2026, 6, 15)
    assert normalize_range_start(day) == datetime(2026, 6, 15, 0, 0, 0)


def test_normalize_range_end_date_only_includes_whole_day() -> None:
    day = datetime(2026, 6, 15)
    end = normalize_range_end(day)
    assert end == datetime(2026, 6, 15, 23, 59, 59, 999999)


def test_normalize_range_keeps_explicit_time() -> None:
    start = datetime(2026, 6, 15, 10, 30, 0)
    end = datetime(2026, 6, 15, 18, 0, 0)
    assert normalize_range_start(start) == start
    assert normalize_range_end(end) == end


def test_normalize_range_none() -> None:
    assert normalize_range_start(None) is None
    assert normalize_range_end(None) is None
