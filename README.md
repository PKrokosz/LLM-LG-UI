# Gothic LARP Q&A UI

Prosty interfejs Gradio do zadawania pytań na podstawie podręczników w formacie Markdown.
Aplikacja przy starcie automatycznie wczytuje wszystkie pliki `.md` z katalogu `data/`
 i buduje indeks BM25. Zapytania są wysyłane do lokalnego serwera LLM.

## Wymagania

- Python 3.10+
- działający serwer LLM (np. `llama.cpp` zgodny z API OpenAI)
- gradio
- rank_bm25
- requests
- unidecode
- rapidfuzz

## Instalacja

```bash
pip install -r requirements.txt
```

## Przygotowanie danych

1. Umieść podręczniki w formacie Markdown w katalogu `data/`.
2. W pliku `data/questions.txt` umieść przykładowe pytania (po jednym w linii) –
   służą do parsowania intencji użytkownika.

## Uruchomienie

```bash
python -m src.app
```

Po uruchomieniu pojawi się pole do wpisania pytania. W odpowiedzi zobaczysz:

- dopasowane pytanie z parsera (z wartością pewności),
- odpowiedź modelu (format Markdown),
- fragmenty źródłowe użyte do odpowiedzi.

Każde zapytanie wraz z wzbogaconym promptem i odpowiedzią trafia do pliku `log.txt`
(w katalogu głównym) – ułatwia to debugowanie.

## Testy

```bash
pytest
```
