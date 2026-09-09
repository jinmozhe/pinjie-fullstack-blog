import re
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from .error_codes import ErrorCode

T = TypeVar("T")
_CHINESE_TEXT = re.compile(r"[\u3400-\u4dbf\u4e00-\u9fff]")


def public_message(message: str, *, fallback: str) -> str:
    return message if _CHINESE_TEXT.search(message) else fallback


class ResponseModel(BaseModel, Generic[T]):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    data: T
    request_id: str


class ErrorResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: str
    message: str
    details: Any | None = None
    request_id: str


def success_response(*, data: T, request_id: str, message: str = "操作成功") -> ResponseModel[T]:
    return ResponseModel(
        code=ErrorCode.OK,
        message=public_message(message, fallback="操作成功"),
        data=data,
        request_id=request_id,
    )


class ValidationErrorDetail(BaseModel):
    loc: list[str | int] = Field(default_factory=list)
    msg: str
    type: str


__all__ = ["ErrorResponse", "ResponseModel", "ValidationErrorDetail", "public_message", "success_response"]
