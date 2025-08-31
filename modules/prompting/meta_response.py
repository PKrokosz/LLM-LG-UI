"""Helpers for meta-level responses such as self-introduction."""

# H1.4: self-introduction in tutor style

def with_introduction(message: str) -> str:
    """Prefix message with a friendly tutor-style introduction."""
    intro = "Cześć! Jestem twój przyjazny tutor Gothic LARP."
    return f"{intro} {message}"
