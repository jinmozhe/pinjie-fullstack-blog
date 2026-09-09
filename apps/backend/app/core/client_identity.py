from ua_parser import parse

_MAX_DEVICE_NAME_LENGTH = 100
_MAX_FAMILY_LENGTH = 48
_UNINFORMATIVE_FAMILIES = frozenset({"generic smartphone", "other"})
_BROWSER_ALIASES = {
    "Chrome Mobile": "Chrome",
    "Chrome Mobile iOS": "Chrome",
    "Edge Mobile": "Edge",
    "Firefox iOS": "Firefox",
    "Mobile Safari": "Safari",
}
_OS_ALIASES = {
    "Chrome OS": "ChromeOS",
    "Mac OS X": "macOS",
}


def _display_family(family: str | None, aliases: dict[str, str]) -> str | None:
    if family is None:
        return None
    normalized = " ".join(family.split())
    if not normalized or normalized.casefold() in _UNINFORMATIVE_FAMILIES:
        return None
    return aliases.get(normalized, normalized)[:_MAX_FAMILY_LENGTH]


def session_device_name(user_agent_summary: str | None) -> str | None:
    if user_agent_summary is None or not user_agent_summary.strip():
        return None

    result = parse(user_agent_summary)
    browser = _display_family(
        result.user_agent.family if result.user_agent is not None else None,
        _BROWSER_ALIASES,
    )
    operating_system = _display_family(
        result.os.family if result.os is not None else None,
        _OS_ALIASES,
    )
    components = [component for component in (browser, operating_system) if component is not None]
    if not components:
        return None
    return " · ".join(components)[:_MAX_DEVICE_NAME_LENGTH]


__all__ = ["session_device_name"]
