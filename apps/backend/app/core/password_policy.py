PASSWORD_MIN_LENGTH = 6
PASSWORD_MAX_LENGTH = 64


def validate_new_password_length(value: str) -> str:
    if not PASSWORD_MIN_LENGTH <= len(value) <= PASSWORD_MAX_LENGTH:
        raise ValueError(f"密码长度必须为 {PASSWORD_MIN_LENGTH} 至 {PASSWORD_MAX_LENGTH} 个字符")
    return value


__all__ = ["PASSWORD_MAX_LENGTH", "PASSWORD_MIN_LENGTH", "validate_new_password_length"]
