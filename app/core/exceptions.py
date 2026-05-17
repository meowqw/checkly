"""Доменные исключения приложения."""


class AppError(Exception):
    """Базовое исключение приложения."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Ресурс не найден"):
        super().__init__(message, status_code=404)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Требуется авторизация"):
        super().__init__(message, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Доступ запрещён"):
        super().__init__(message, status_code=403)


class ConflictError(AppError):
    def __init__(self, message: str = "Конфликт данных"):
        super().__init__(message, status_code=409)


class ExternalServiceError(AppError):
    def __init__(self, message: str = "Ошибка внешнего сервиса"):
        super().__init__(message, status_code=502)
