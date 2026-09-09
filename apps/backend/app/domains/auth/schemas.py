import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.password_policy import PASSWORD_MAX_LENGTH, PASSWORD_MIN_LENGTH

_USERNAME_PATTERN = re.compile(r"^[a-z0-9._-]{3,50}$")


def normalize_username(value: str) -> str:
    normalized = value.strip().lower()
    if not _USERNAME_PATTERN.fullmatch(normalized):
        raise ValueError("username must be 3-50 lowercase letters, digits, dot, underscore, or hyphen")
    return normalized


class UserRegisterIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str = Field(
        min_length=PASSWORD_MIN_LENGTH,
        max_length=PASSWORD_MAX_LENGTH,
        description="登录密码，长度为 6 至 64 个字符",
    )
    display_name: str | None = Field(default=None, max_length=100)
    email: str | None = Field(default=None, max_length=320)

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return normalize_username(value)

    @field_validator("email")
    @classmethod
    def normalize_email(cls, value: str | None) -> str | None:
        return value.strip().lower() if value else None


class UserLoginIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    username: str
    password: str = Field(min_length=1, max_length=PASSWORD_MAX_LENGTH, description="登录密码，最多 64 个字符")

    @field_validator("username")
    @classmethod
    def validate_username(cls, value: str) -> str:
        return normalize_username(value)


class UserPrincipalOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    id: uuid.UUID
    username: str
    display_name: str | None
    email: str | None
    avatar: str | None = Field(default=None, description="用户头像站内资源路径")
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserAuthSessionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    principal: UserPrincipalOut
    session_id: uuid.UUID
    access_expires_at: datetime
    idle_expires_at: datetime
    absolute_expires_at: datetime


class RefreshSessionOut(BaseModel):
    model_config = ConfigDict(extra="forbid")

    session_id: uuid.UUID
    access_expires_at: datetime
    idle_expires_at: datetime
    absolute_expires_at: datetime


__all__ = [
    "RefreshSessionOut",
    "UserAuthSessionOut",
    "UserLoginIn",
    "UserPrincipalOut",
    "UserRegisterIn",
    "normalize_username",
]
