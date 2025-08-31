"""Prompt templates and few-shot examples for the assistant."""
from typing import List, Tuple

# H1.1: system prompt in a more natural human tone
SYSTEM_PROMPT = (
    "Jestem przyjaznym tutorem Gothic LARP dla nowego gracza. "
    "Tłumaczę krok po kroku i korzystam wyłącznie z dostarczonego kontekstu."
)

# H1.2: few-shot Q&A examples for context prompting
FEWSHOT_QA: List[Tuple[str, str]] = [
    (
        "Jak działa magia ognia?",
        "Na początek, \"ognia chwała\" budzi płomień w dłoni. Źródło: Strona 12 – Sekcja Magia ognia.",
    ),
    (
        "Co robi nowicjusz na początku?",
        "Nowy gracz najpierw \"uczy się podstaw przy ognisku\". Źródło: Strona 3 – Sekcja Wprowadzenie.",
    ),
]
