"""Роутер аутентификации."""
from fastapi import APIRouter, Depends

from app.api.deps import DbSession
from app.dto.auth import AuthResponseDTO, LoginRequestDTO, RegisterRequestDTO
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponseDTO)
def register(dto: RegisterRequestDTO, db: DbSession) -> AuthResponseDTO:
    return AuthService(db).register(dto)


@router.post("/login", response_model=AuthResponseDTO)
def login(dto: LoginRequestDTO, db: DbSession) -> AuthResponseDTO:
    return AuthService(db).login(dto)
