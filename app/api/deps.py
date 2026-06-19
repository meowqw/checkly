"""Зависимости FastAPI."""
from typing import Annotated

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.dates import resolve_timezone
from app.core.exceptions import UnauthorizedError
from app.core.security import decode_access_token
from app.database import get_db
from app.database.models import User
from app.repositories.user_repository import UserRepository

DbSession = Annotated[Session, Depends(get_db)]

bearer_scheme = HTTPBearer(
    auto_error=False,
    description="JWT access token из ответа /v1/auth/login или /v1/auth/register",
)

XTimezoneHeader = Annotated[
    str | None,
    Header(
        alias="X-Timezone",
        description="Часовой пояс IANA (например Europe/Moscow). Опционально.",
    ),
]


def get_request_timezone(x_timezone: XTimezoneHeader = None) -> str:
    return resolve_timezone(x_timezone)


RequestTimezone = Annotated[str, Depends(get_request_timezone)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)] = None,
) -> User:
    if not credentials:
        raise UnauthorizedError()
    token = credentials.credentials
    try:
        payload = decode_access_token(token)
    except ValueError as exc:
        raise UnauthorizedError("Недействительный токен") from exc

    user_uid = payload.get("sub")
    if not user_uid:
        raise UnauthorizedError()

    user = UserRepository(db).get_by_uid(str(user_uid))
    if not user:
        raise UnauthorizedError("Пользователь не найден")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_user_timezone(
    db: DbSession,
    user: CurrentUser,
    x_timezone: XTimezoneHeader = None,
) -> str:
    stored = resolve_timezone(user.timezone)
    if x_timezone:
        header_tz = resolve_timezone(x_timezone)
        if header_tz != stored:
            user.timezone = header_tz
            db.commit()
            return header_tz
    return stored


UserTimezone = Annotated[str, Depends(get_user_timezone)]
