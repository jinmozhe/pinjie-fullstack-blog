from dataclasses import dataclass

from loguru import logger
from redis.asyncio import Redis
from redis.exceptions import RedisError

from app.core.error_codes import ErrorCode
from app.core.exceptions import AppException

_FIXED_WINDOW_SCRIPT = """
local current = redis.call('INCR', KEYS[1])
if current == 1 then
  redis.call('EXPIRE', KEYS[1], ARGV[1])
end
local ttl = redis.call('TTL', KEYS[1])
return {current, ttl}
"""


@dataclass(frozen=True, slots=True)
class RateLimitState:
    count: int
    retry_after: int


async def enforce_rate_limit(redis: Redis | None, *, key: str, limit: int, window_seconds: int) -> RateLimitState:
    if redis is None:
        raise AppException(
            status_code=503,
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="认证服务暂时不可用",
        )
    try:
        raw = await redis.eval(_FIXED_WINDOW_SCRIPT, 1, key, window_seconds)
    except RedisError as exc:
        raise AppException(
            status_code=503,
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="认证服务暂时不可用",
        ) from exc
    if not isinstance(raw, (list, tuple)) or len(raw) != 2:
        raise AppException(
            status_code=503,
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="认证服务返回了无效的限流状态",
        )
    state = RateLimitState(count=int(raw[0]), retry_after=max(1, int(raw[1])))
    if state.count > limit:
        raise AppException(
            status_code=429,
            code=ErrorCode.RATE_LIMITED,
            message="请求过于频繁",
            details={"retry_after": state.retry_after},
            headers={"Retry-After": str(state.retry_after)},
        )
    return state


async def acquire_refresh_lock(redis: Redis | None, *, key: str, owner: str, ttl_seconds: int = 10) -> bool:
    if redis is None:
        raise AppException(
            status_code=503,
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="认证服务暂时不可用",
        )
    try:
        return bool(await redis.set(key, owner, ex=ttl_seconds, nx=True))
    except RedisError as exc:
        raise AppException(
            status_code=503,
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message="认证服务暂时不可用",
        ) from exc


async def release_refresh_lock(redis: Redis | None, *, key: str, owner: str) -> None:
    if redis is None:
        return
    script = "if redis.call('GET', KEYS[1]) == ARGV[1] then return redis.call('DEL', KEYS[1]) else return 0 end"
    try:
        await redis.eval(script, 1, key, owner)
    except RedisError as exc:
        logger.bind(cache_key=key).opt(exception=exc).critical("failed to release authentication refresh lock")


__all__ = ["RateLimitState", "acquire_refresh_lock", "enforce_rate_limit", "release_refresh_lock"]
