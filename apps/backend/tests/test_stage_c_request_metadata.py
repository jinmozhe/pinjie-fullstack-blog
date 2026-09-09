from fastapi import FastAPI, Request

from app.core.config import Settings
from app.core.request_metadata import trusted_client_ip
from tests.conftest import TEST_SECRETS


def _request(*, peer: str, forwarded: str | None, trusted: list[str]) -> Request:
    app = FastAPI()
    app.state.settings = Settings(TRUSTED_PROXY_CIDRS=trusted, **TEST_SECRETS)
    headers = [] if forwarded is None else [(b"x-forwarded-for", forwarded.encode("ascii"))]
    return Request(
        {
            "type": "http",
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/",
            "raw_path": b"/",
            "query_string": b"",
            "headers": headers,
            "client": (peer, 12345),
            "server": ("testserver", 80),
            "app": app,
        }
    )


def test_untrusted_peer_cannot_spoof_forwarded_for() -> None:
    request = _request(peer="203.0.113.20", forwarded="198.51.100.3", trusted=["127.0.0.1/32"])
    assert trusted_client_ip(request) == "203.0.113.20"


def test_trusted_proxy_chain_selects_first_untrusted_hop_from_right() -> None:
    request = _request(
        peer="127.0.0.1",
        forwarded="198.51.100.9, 10.0.0.4",
        trusted=["127.0.0.1/32", "10.0.0.0/8"],
    )
    assert trusted_client_ip(request) == "198.51.100.9"


def test_malformed_forwarding_header_falls_back_to_peer() -> None:
    request = _request(peer="127.0.0.1", forwarded="not-an-ip", trusted=["127.0.0.1/32"])
    assert trusted_client_ip(request) == "127.0.0.1"
