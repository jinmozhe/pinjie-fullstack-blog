import json

import pytest
from fastapi import Request
from starlette.responses import Response

from app.core.middleware import request_context_middleware
from app.core.payload_sanitizer import (
    MAX_REQUEST_BODY_CHARS,
    TRUNCATION_MARKER,
    capture_error_request_body,
    is_sensitive_route,
)
from scripts.consume_request_logs import _request_log


def _request(body: bytes, *, path: str = "/api/v1/users", content_type: str = "application/json") -> Request:
    async def receive() -> dict[str, object]:
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "POST",
            "scheme": "http",
            "path": path,
            "raw_path": path.encode("ascii"),
            "query_string": b"",
            "headers": [
                (b"content-type", content_type.encode("ascii")),
                (b"content-length", str(len(body)).encode("ascii")),
            ],
            "client": ("127.0.0.1", 12345),
            "server": ("testserver", 80),
        },
        receive=receive,
    )


def test_sensitive_route_matching_normalizes_trailing_slash() -> None:
    assert is_sensitive_route("/api/v1/auth/login/") is True
    assert is_sensitive_route("/api/v1/users/me/password") is True
    assert is_sensitive_route("/api/v1/users") is False


def test_request_log_consumer_maps_optional_body() -> None:
    item = _request_log(
        {
            "request_id": "request-1",
            "trace_id": "trace-1",
            "method": "POST",
            "route_template": "/api/v1/users",
            "status_code": "422",
            "duration_ms": "12",
            "principal_type": "user",
            "principal_digest": "digest",
            "release_version": "test",
            "occurred_at": "2026-08-20T00:00:00+00:00",
            "request_body": '{"password":"***"}',
        }
    )

    assert item.request_body == '{"password":"***"}'


@pytest.mark.asyncio
async def test_success_and_non_json_requests_are_not_captured() -> None:
    request = _request(b'{"username":"alice"}')
    assert await capture_error_request_body(request, status_code=200, route_template="/api/v1/users") is None
    assert (
        await capture_error_request_body(
            _request(b"name=alice", content_type="application/x-www-form-urlencoded"),
            status_code=422,
            route_template="/api/v1/users",
        )
        is None
    )


@pytest.mark.asyncio
async def test_sensitive_route_skips_body_even_for_error() -> None:
    request = _request(b'{"password":"plain-text"}', path="/api/v1/auth/login")

    assert await capture_error_request_body(request, status_code=422, route_template="/api/v1/auth/login") is None


@pytest.mark.asyncio
async def test_error_body_is_recursively_redacted() -> None:
    request = _request(
        json.dumps(
            {
                "profile": {"display_name": "Alice", "password": "plain-text"},
                "items": [{"token": "secret-token", "quantity": 2}],
            }
        ).encode()
    )

    result = await capture_error_request_body(request, status_code=422, route_template="/api/v1/users")

    assert result == '{"profile":{"display_name":"Alice","password":"***"},"items":[{"token":"***","quantity":2}]}'


@pytest.mark.asyncio
async def test_large_content_length_short_circuits_to_marker() -> None:
    body = b"{" + b'"comment":"' + b"x" * MAX_REQUEST_BODY_CHARS + b'"}'
    request = _request(body)

    result = await capture_error_request_body(request, status_code=500, route_template="/api/v1/comments")

    assert result == TRUNCATION_MARKER


@pytest.mark.asyncio
async def test_serialized_body_is_truncated_to_maximum_length() -> None:
    request = _request(b'{"comment":"' + b"x" * 5000 + b'"}')
    request.scope["headers"] = [header for header in request.scope["headers"] if header[0] != b"content-length"]

    result = await capture_error_request_body(request, status_code=500, route_template="/api/v1/comments")

    assert result is not None
    assert len(result) == MAX_REQUEST_BODY_CHARS
    assert result.endswith(TRUNCATION_MARKER)


@pytest.mark.asyncio
async def test_request_middleware_forwards_sanitized_error_body(monkeypatch) -> None:
    request = _request(b'{"password":"plain-text","name":"Alice"}')
    published = []

    async def fake_publish(*args, **kwargs) -> None:
        published.append(kwargs)

    async def call_next(received: Request) -> Response:
        await received.body()
        return Response(status_code=422)

    monkeypatch.setattr("app.core.middleware.publish_request_log", fake_publish)

    response = await request_context_middleware(request, call_next)

    assert response.status_code == 422
    assert published[0]["request_body"] == '{"password":"***","name":"Alice"}'
