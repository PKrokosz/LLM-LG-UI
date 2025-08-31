# Parser intencji użytkownika

**Cel:** Zbudować parser intencji użytkownika korzystający z pytań w plikach `FAQ LARP GOTHIC.md` oraz `rules.md`.

**Opis:**
- Na podstawie treści pytań z obu plików przygotować listę kategorii, np. "walka", "alchemia", "mechanika śmierci".
- Parser powinien dla danego pytania zwracać:
  - typ pytania (kategoria)
  - dopasowany alias promptowy wykorzystywany w interfejsie LLM.

**Kryteria akceptacji:**
- Zebrane i opisane co najmniej podstawowe kategorie pytań.
- Dla każdej kategorii ustalony alias promptowy.
- Dodane testy weryfikujące poprawne rozpoznawanie kategorii na przykładowych pytaniach.
