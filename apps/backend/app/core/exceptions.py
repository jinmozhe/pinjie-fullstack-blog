from typing import Any

from .error_codes import ErrorCode


class AppException(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        code: ErrorCode | str,
        message: str,
        details: Any = None,
        headers: dict[str, str] | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = str(code)
        self.message = message
        self.details = details
        self.headers = headers or {}
