"""DTO для счетов."""
from pydantic import BaseModel, Field


class AccountDTO(BaseModel):
    id: str
    name: str
    balance: int


class AccountsListResponseDTO(BaseModel):
    accounts: list[AccountDTO]


class CreateAccountRequestDTO(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    balance: int = 0


class UpdateAccountRequestDTO(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    balance: int | None = None


class AccountResponseDTO(BaseModel):
    account: AccountDTO


class SuccessResponseDTO(BaseModel):
    success: bool = True
