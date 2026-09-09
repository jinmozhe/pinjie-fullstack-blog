from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class SystemStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["available", "unavailable"]


class SystemCapabilitiesRead(BaseModel):
    model_config = ConfigDict(extra="forbid")

    registration_enabled: bool = Field(description="是否允许 Web 公开注册普通用户")


class LiveStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["alive"]


class ReadinessStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: Literal["ready", "unavailable"]
    checks: dict[str, str]
