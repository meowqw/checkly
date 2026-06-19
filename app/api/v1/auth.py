"""Роутер аутентификации."""
from fastapi import APIRouter

from app.api.deps import DbSession, RequestTimezone
from app.dto.auth import AuthResponseDTO, LoginRequestDTO, RegisterRequestDTO
from app.openapi import COMMON_ERROR_RESPONSES
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/register",
    response_model=AuthResponseDTO,
    summary="Регистрация",
    description="Создаёт пользователя и сразу возвращает JWT-токен.",
    responses={400: COMMON_ERROR_RESPONSES[400], 409: COMMON_ERROR_RESPONSES[409]},
)
def register(dto: RegisterRequestDTO, db: DbSession, tz: RequestTimezone) -> AuthResponseDTO:
    return AuthService(db).register(dto, tz)


@router.post(
    "/login",
    response_model=AuthResponseDTO,
    summary="Вход",
    description="Проверяет логин и пароль, возвращает JWT-токен.",
    responses={401: COMMON_ERROR_RESPONSES[401]},
)
def login(dto: LoginRequestDTO, db: DbSession, tz: RequestTimezone) -> AuthResponseDTO:
    return AuthService(db).login(dto, tz)
