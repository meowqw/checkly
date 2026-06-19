"""DTO для аутентификации."""
from pydantic import BaseModel, EmailStr, Field


class RegisterRequestDTO(BaseModel):
    email: EmailStr = Field(description="Email пользователя")
    login: str = Field(min_length=2, max_length=100, description="Логин (уникальный)")
    password: str = Field(min_length=6, max_length=128, description="Пароль")


class LoginRequestDTO(BaseModel):
    login: str = Field(description="Логин")
    password: str = Field(description="Пароль")


class UserDTO(BaseModel):
    id: str = Field(description="UUID пользователя")
    email: str = Field(description="Email")
    login: str = Field(description="Логин")
    timezone: str = Field(default="Europe/Moscow", description="Часовой пояс IANA")


class AuthResponseDTO(BaseModel):
    user: UserDTO = Field(description="Данные пользователя")
    access_token: str = Field(description="JWT для заголовка Authorization: Bearer …")
