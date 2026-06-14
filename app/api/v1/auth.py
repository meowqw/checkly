"""Роутер аутентификации."""
from fastapi import APIRouter, Depends

from app.api.deps import DbSession, RequestTimezone
from app.dto.auth import AuthResponseDTO, LoginRequestDTO, RegisterRequestDTO
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponseDTO)
def register(dto: RegisterRequestDTO, db: DbSession, tz: RequestTimezone) -> AuthResponseDTO:
    return AuthService(db).register(dto, tz)


@router.post("/login", response_model=AuthResponseDTO)
def login(dto: LoginRequestDTO, db: DbSession, tz: RequestTimezone) -> AuthResponseDTO:
    return AuthService(db).login(dto, tz)
