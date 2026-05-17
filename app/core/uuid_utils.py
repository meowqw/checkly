"""Утилиты для генерации публичных UUID."""
import uuid


def new_uid() -> str:
    return str(uuid.uuid4())
