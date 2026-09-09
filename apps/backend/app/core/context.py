from contextvars import ContextVar

from .identifiers import new_uuid7

request_id_context: ContextVar[str] = ContextVar("request_id", default="")
trace_id_context: ContextVar[str] = ContextVar("trace_id", default="")


def current_request_id() -> str:
    return request_id_context.get() or str(new_uuid7())


def current_trace_id() -> str:
    return trace_id_context.get() or str(new_uuid7())
