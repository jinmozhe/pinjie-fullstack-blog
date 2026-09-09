import uuid

from app.core.identifiers import new_uuid7


def test_new_uuid7_returns_standard_library_uuid() -> None:
    value = new_uuid7()
    assert type(value) is uuid.UUID
    assert value.version == 7


def test_new_uuid7_is_unique_and_time_ordered() -> None:
    values = [new_uuid7() for _ in range(100)]
    assert len(set(values)) == len(values)
    assert values == sorted(values)
