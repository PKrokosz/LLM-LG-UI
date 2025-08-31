# Gothic LARP Q&A UI

Interaktywny UI do zadawania pytań na podstawie markdownowego podręcznika Gothic LARP, z wykorzystaniem lokalnego LLM (Phi-3) i RAG (BM25 + context-injection).

## Wymagania

- Python 3.10+
- llama-cpp-python (serwer LLM)
- gradio
- rank_bm25
- requests
- unidecode

## Instalacja

```bash
pip install -r requirements.txt
# opcjonalnie, dla lokalnego serwera LLM
pip install llama-cpp-python
```

## Uruchomienie

```bash
python gothic_rag_ui_parser.py
```

Aplikacja nasłuchuje domyślnie pod adresem [http://localhost:7860](http://localhost:7860). Upewnij się, że serwer LLM (np. `llama-cpp-python` z modelem Phi-3) jest uruchomiony i dostępny pod adresem ustawionym w `LLAMA_BASE_URL` (domyślnie `http://127.0.0.1:8000`).

## Przykładowe pytania

- Jak się walczy?
- Co daje karta łowcy?
- Ile many kosztuje rzut runą?

### Format odpowiedzi

```
Odpowiedź: <2–4 zdania z podręcznika; jeśli brak — 'Nie ma tego w podręczniku.'>
Cytat: "<krótki cytat z kontekstu>" (opcjonalnie)
Źródła: [Strona X — Sekcja: Y]; [Strona ...]
```

