"""Helpers for meta-level responses such as self-introduction."""

# H1.4: self-introduction as Pomocnik Gothic LARP

def with_introduction(message: str) -> str:
    """Prefix message with a friendly self-introduction."""
    intro = "Cześć! Jestem Pomocnik Gothic LARP."
    return f"{intro} {message}"
