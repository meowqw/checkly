"""DTO для счетов."""
from pydantic import BaseModel, Field


class AccountMemberDTO(BaseModel):
    id: str = Field(description="UUID пользователя")
    login: str = Field(description="Логин")
    role: str = Field(description="Роль на счёте: owner | member")


class AccountDTO(BaseModel):
    id: str = Field(description="UUID счёта")
    name: str = Field(description="Название счёта")
    balance: int = Field(description="Баланс в копейках")
    members: list[AccountMemberDTO] = Field(
        default_factory=list, description="Участники счёта"
    )


class AccountsListResponseDTO(BaseModel):
    accounts: list[AccountDTO] = Field(description="Список счетов пользователя")


class CreateAccountRequestDTO(BaseModel):
    name: str = Field(min_length=1, max_length=255, description="Название счёта")
    balance: int = Field(default=0, description="Начальный баланс в копейках")


class UpdateAccountRequestDTO(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255, description="Новое название")
    balance: int | None = Field(default=None, description="Новый баланс в копейках")


class AccountResponseDTO(BaseModel):
    account: AccountDTO = Field(description="Счёт")


class CreateAccountInviteResponseDTO(BaseModel):
    token: str = Field(description="Одноразовый токен приглашения")


class JoinAccountRequestDTO(BaseModel):
    token: str = Field(min_length=1, max_length=36, description="Токен приглашения")


class SuccessResponseDTO(BaseModel):
    success: bool = Field(default=True, description="Операция выполнена успешно")
