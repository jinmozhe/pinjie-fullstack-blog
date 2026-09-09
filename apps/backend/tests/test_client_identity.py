import pytest

from app.core.client_identity import session_device_name


@pytest.mark.parametrize(
    ("user_agent", "expected"),
    [
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36",
            "Chrome · Windows",
        ),
        (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0",
            "Edge · Windows",
        ),
        (
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:142.0) Gecko/20100101 Firefox/142.0",
            "Firefox · Ubuntu",
        ),
        (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Safari/605.1.15",
            "Safari · macOS",
        ),
        (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1",
            "Safari · iOS",
        ),
        (
            "Mozilla/5.0 (Linux; Android 16; Pixel 9 Pro Build/BP2A) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36",
            "Chrome · Android",
        ),
        ("curl/8.14.1", "curl"),
    ],
)
def test_session_device_name_formats_stable_browser_and_os_families(user_agent: str, expected: str) -> None:
    assert session_device_name(user_agent) == expected


@pytest.mark.parametrize("user_agent", [None, "", "   ", "Mozilla/5.0", "UnknownAgent"])
def test_session_device_name_returns_none_without_useful_identity(user_agent: str | None) -> None:
    assert session_device_name(user_agent) is None
