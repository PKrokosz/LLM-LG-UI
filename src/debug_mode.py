"""Global toggle for debug mode in the UI."""

DEBUG_MODE = False


def set_debug(value: bool) -> None:
    """Enable or disable debug mode."""
    global DEBUG_MODE
    DEBUG_MODE = bool(value)


def is_debug() -> bool:
    """Return whether debug mode is enabled."""
    return DEBUG_MODE
