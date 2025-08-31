"""Apply persona-based style instructions to prompts."""
from .persona_selector import select_persona


def apply_style(base_prompt: str, mode: str) -> str:
    """Append style instructions for the chosen persona to the base prompt."""
    style = select_persona(mode)
    return f"{base_prompt}\n\n{style}"
