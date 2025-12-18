from typing import Any
from fastapi import HTTPException


class BfoTooManyRequestsException(HTTPException):
    """Исключение для Too Many Requests"""

    def __init__(self, detail: Any = "Слишком много запросов", headers: dict = None):
        super().__init__(
            status_code=429,
            detail={"detail": detail},
            headers=headers,
        )


class BfoApiException(HTTPException):
    """Базовое исключение для ошибок BFO API"""

    def __init__(self, status_code: int, detail: dict):
        super().__init__(status_code=status_code, detail=detail)
