"""Unit: JWT и пароли."""
import pytest
from jose import jwt

from app.config import get_settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_and_verify_password() -> None:
    hashed = hash_password("secret123")
    assert hashed != "secret123"
    assert verify_password("secret123", hashed) is True
    assert verify_password("wrong", hashed) is False


def test_create_and_decode_access_token() -> None:
    token = create_access_token("user-uid-1")
    payload = decode_access_token(token)
    assert payload["sub"] == "user-uid-1"
    assert "exp" in payload


def test_decode_invalid_token_raises() -> None:
    with pytest.raises(ValueError, match="Недействительный"):
        decode_access_token("not.a.jwt")


def test_decode_tampered_token_raises() -> None:
    settings = get_settings()
    token = create_access_token("user-uid-1")
    # подпись другим секретом
    bad = jwt.encode({"sub": "user-uid-1"}, "wrong-secret", algorithm=settings.jwt_algorithm)
    with pytest.raises(ValueError):
        decode_access_token(bad)
    assert token  # token создан валидно
