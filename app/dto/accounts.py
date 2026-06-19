"""DTO для счетов."""
from pydantic import BaseModel, Field


class AccountDTO(BaseModel):
    id: str = Field(description="UUID счёта")
    name: str = Field(description="Название счёта")
    balance: int = Field(description="Баланс в копейках")


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


class SuccessResponseDTO(BaseModel):
    success: bool = Field(default=True, description="Операция выполнена успешно")
