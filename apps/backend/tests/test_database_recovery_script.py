import pytest

from scripts.verify_local_database_recovery import assert_safe_database_name, parse_test_database_url


def test_parse_test_database_url_accepts_isolated_local_database() -> None:
    target = parse_test_database_url("postgresql+asyncpg://tester:secret@localhost:5433/pinjie_recovery_test")

    assert target.hostname == "localhost"
    assert target.port == 5433
    assert target.username == "tester"
    assert target.database == "pinjie_recovery_test"
    assert target.url_for("pinjie_restore_test").endswith("/pinjie_restore_test")


@pytest.mark.parametrize(
    "url",
    [
        None,
        "postgresql://tester:secret@localhost/pinjie_test",
        "postgresql+asyncpg://tester:secret@database.example.com/pinjie_test",
        "postgresql+asyncpg://tester@localhost/pinjie_test",
        "postgresql+asyncpg://tester:secret@localhost/pinjie_dev",
    ],
)
def test_parse_test_database_url_rejects_unsafe_targets(url: str | None) -> None:
    with pytest.raises(ValueError):
        parse_test_database_url(url)


@pytest.mark.parametrize("name", ["pinjie_test", "a1_test", "recovery_case_test"])
def test_safe_database_names_are_accepted(name: str) -> None:
    assert_safe_database_name(name, "database")


@pytest.mark.parametrize("name", ["pinjie_dev", "_test", "Pinjie_test", "pinjie-test", "1pinjie_test"])
def test_unsafe_database_names_are_rejected(name: str) -> None:
    with pytest.raises(ValueError):
        assert_safe_database_name(name, "database")
