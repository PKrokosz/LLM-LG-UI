"""Select response style based on persona."""

PERSONA_STYLES = {
    "gracz": "Odpowiadaj krótko i praktycznie, skupiając się na działaniu.",
    "mg": "Odpowiadaj analitycznie i opisowo, tłumacząc decyzje oraz tło.",
}


def select_persona(mode: str) -> str:
    """Return style instruction for a given persona mode."""
    return PERSONA_STYLES.get(mode.lower(), PERSONA_STYLES["gracz"])
