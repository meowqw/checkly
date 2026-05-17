"""Репозиторий пользователей."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database.models import User


class UserRepository:
    def __init__(self, db: Session):
        self._db = db

    def get_by_uid(self, uid: str) -> User | None:
        return self._db.scalar(select(User).where(User.uid == uid))

    def get_by_login(self, login: str) -> User | None:
        return self._db.scalar(select(User).where(User.login == login))

    def get_by_email(self, email: str) -> User | None:
        return self._db.scalar(select(User).where(User.email == email))

    def get_by_id(self, user_id: int) -> User | None:
        return self._db.get(User, user_id)

    def create(self, user: User) -> User:
        self._db.add(user)
        self._db.flush()
        return user
