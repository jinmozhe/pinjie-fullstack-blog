from app.core.security import constant_time_token_matches, new_opaque_token, token_digest


def new_csrf_token(key: str) -> tuple[str, str]:
    token = new_opaque_token()
    return token, token_digest(token, key)


def verify_csrf_token(token: str, expected_digest: str, key: str) -> bool:
    return constant_time_token_matches(token, expected_digest, key)


__all__ = ["new_csrf_token", "verify_csrf_token"]
