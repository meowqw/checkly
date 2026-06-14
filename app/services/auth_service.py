"""Сервис аутентификации."""
from sqlalchemy.orm import Session

from app.core.dates import resolve_timezone
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import create_access_token, hash_password, verify_password
from app.core.uuid_utils import new_uid
from app.database.models import User
from app.dto.auth import AuthResponseDTO, LoginRequestDTO, RegisterRequestDTO, UserDTO
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(self, db: Session):
        self._users = UserRepository(db)
        self._db = db

    def register(self, dto: RegisterRequestDTO, timezone: str) -> AuthResponseDTO:
        if self._users.get_by_email(dto.email):
            raise ConflictError("Email уже занят")
        if self._users.get_by_login(dto.login):
            raise ConflictError("Логин уже занят")

        user = User(
            uid=new_uid(),
            email=dto.email,
            login=dto.login,
            password=hash_password(dto.password),
            timezone=resolve_timezone(timezone),
        )
        self._users.create(user)
        self._db.commit()
        self._db.refresh(user)
        return self._build_auth_response(user)

    def login(self, dto: LoginRequestDTO, timezone: str) -> AuthResponseDTO:
        user = self._users.get_by_login(dto.login)
        if not user or not verify_password(dto.password, user.password):
            raise UnauthorizedError("Неверный логин или пароль")
        resolved = resolve_timezone(timezone)
        if user.timezone != resolved:
            user.timezone = resolved
            self._db.commit()
            self._db.refresh(user)
        return self._build_auth_response(user)

    def _build_auth_response(self, user: User) -> AuthResponseDTO:
        token = create_access_token(user.uid)
        return AuthResponseDTO(
            user=UserDTO(
                id=user.uid,
                email=user.email,
                login=user.login,
                timezone=user.timezone,
            ),
            access_token=token,
        )
