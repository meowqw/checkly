"""DTO для аутентификации."""
from pydantic import BaseModel, EmailStr, Field


class RegisterRequestDTO(BaseModel):
    email: EmailStr
    login: str = Field(min_length=2, max_length=100)
    password: str = Field(min_length=6, max_length=128)


class LoginRequestDTO(BaseModel):
    login: str
    password: str


class UserDTO(BaseModel):
    id: str
    email: str
    login: str


class AuthResponseDTO(BaseModel):
    user: UserDTO
    access_token: str
