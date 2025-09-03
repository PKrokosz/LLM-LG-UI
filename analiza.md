# Analiza repozytorium

## Pliki główne
- **README.md** – opisuje cel projektu, wymagania i sposób uruchomienia.
- **REPORT.md** – istniejący raport z inwentaryzacją i rekomendacjami.
- **metrics_report.md** – szkic tabeli porównującej skuteczność retrieverów.
- **settings.yaml** – parametry aplikacji (progi pewności i ustawienia retrievera).
- **requirements.txt** – zależności środowiska uruchomieniowego.
- **requirements-dev.txt** – paczki potrzebne do testów i lintów.
- **.pre-commit-config.yaml** – konfiguracja narzędzi flake8 i podstawowych hooków.
- **.gitignore** – ignoruje cache Pythona i plik log.txt.
- **faiss.py** – minimalistyczny stub biblioteki FAISS używany w testach offline.
- **stress_test.py** – skrypt wielowątkowy sprawdzający bezpieczeństwo zapisu logów.
- **log_tester.py** – narzędzie weryfikujące spójność wpisów w log.txt.
- **frequent_questions.json** – lista często zadawanych pytań wyświetlanych w UI.
- **retrieval_tests/test_queries.json** – zbiór zapytań do ręcznego testowania retrieverów.

## Dane (`data/`)
- **PODRECZNIK.md** – główny podręcznik w formacie Markdown wykorzystywany jako korpus.
- **rules.md** – dodatkowy plik z zasadami gry.
- **FAQ.md** – odpowiedzi na najczęstsze pytania.
- **questions.txt** – przykładowe pytania służące do dopasowywania intencji.

## Pakiet `modules`
### `modules/__init__.py`
- Udostępnia główne podpakiety: parser, retrieval, prompting, logic, ui.

### `modules/parser`
- **gothic_rag_ui_parser.py** – kompletne narzędzie do parsowania plików Markdown i obsługi zapytań (starsza wersja aplikacji).
- **__init__.py** – eksport funkcji `md_to_pages` i `normalize`.

### `modules/retrieval`
- **retrieval.py** – dzielenie Markdown na strony i implementacja BM25.
- **retriever_interface.py** – wspólny interfejs retrieverów i fabryka `create_retriever`.
- **retriever_vector.py** – retriever wektorowy oparty o SentenceTransformers i FAISS (z fallbackiem offline).
- **retriever_hybrid.py** – łączy wyniki BM25 i wektorowe metodą RRF.
- **embedder_local.py** – prosty embedder słownikowy do pracy offline.
- **__init__.py** – agreguje klasy i funkcje powyżej.

### `modules/prompting`
- **prompt_templates.py** – systemowy prompt i przykłady few-shot.
- **prompt_enhancer.py** – buduje końcowy prompt z intencją i kontekstem.
- **persona_selector.py** – dobiera styl odpowiedzi w zależności od persony.
- **style_prompting.py** – dokleja instrukcję stylu do promptu.
- **meta_response.py** – dodaje przyjazne wprowadzenie do odpowiedzi.
- **response_formatter.py** – wplata cytaty w odpowiedź modelu.
- **__init__.py** – eksportuje powyższe narzędzia.

### `modules/logic`
- **config.py** – stałe konfiguracyjne (adres serwera LLM, limity tokenów).
- **confidence_mode.py** – weryfikuje czy najwyższy wynik spełnia próg pewności.
- **debug_mode.py** – globalny przełącznik trybu debugowania UI.
- **fallback_logic.py** – zwraca neutralną odpowiedź, gdy brak trafień.
- **utils.py** – normalizacja i tokenizacja tekstu.
- **index_loader.py** – serializacja i ładowanie indeksów BM25/FAISS.
- **intent_embedder.py** – dopasowywanie intencji użytkownika względem katalogu pytań.
- **llm_client.py** – główny przepływ RAG: wyszukiwanie, budowanie promptu, wywołanie LLM i formatowanie odpowiedzi.
- **logger_async.py** – asynchroniczny logger z rotacją plików.
- **metrics_logger.py** – zapis metryk czasowych do pliku JSONL.
- **query_monitor.py** – zapisywanie zapytań i uzupełnianie metryk.
- **__init__.py** – eksportuje najważniejsze funkcje i klasy logiczne.

### `modules/ui`
- **app.py** – uproszczony interfejs Gradio bez trybu debug.
- **gradio_ui.py** – rozbudowana wersja UI z przełącznikiem debugowania i obsługą predefiniowanych pytań.
- **__init__.py** – eksponuje funkcje budowania aplikacji.

## Pakiet `src`
"src" re-eksportuje funkcje z `modules` dla prostszych importów w testach.
- **llm_client.py** – cienka otoczka umożliwiająca łatwe podmiany funkcji w testach.
- Pozostałe pliki (`gradio_ui.py`, `index_loader.py`, `intent_embedder.py`, `meta_response.py`, `persona_selector.py`, `prompt_enhancer.py`, `prompt_templates.py`, `response_formatter.py`, `retrieval.py`, `retriever_hybrid.py`, `retriever_vector.py`, `style_prompting.py`) – importują i udostępniają odpowiadające moduły.

## Testy (`tests/`)
- **test_frequent_questions.py** – sprawdza poprawne wczytanie listy gotowych pytań.
- **test_prompt_enhancer.py** – weryfikuje dodawanie metadanych intencji do promptu.
- **test_response_formatter.py** – testuje wplatanie cytatów w odpowiedź.
- **test_persona_style.py** – upewnia się, że wybór persony zmienia styl odpowiedzi.
- **test_retrieval.py** – kontroluje dzielenie Markdown oraz działanie BM25.
- **test_retriever_hybrid.py** – bada fuzję wyników BM25 i wektorowych.
- **test_intent_embedder.py** – sprawdza dopasowanie intencji do katalogu pytań.
- **test_llm_client.py** – testuje główny przepływ odpowiedzi z mockiem LLM.
- **test_query_monitor.py** – weryfikuje logowanie zapytań i metryk.
- **test_meta_response.py** – potwierdza dodawanie wprowadzenia do odpowiedzi.
- **test_prompt_templates.py** – kontroluje treść promptów i przykładów.
- **test_index_loader.py** – testuje serializację i cache indeksów.

## Inne
- **user_logs/.gitkeep** – pusty plik utrzymujący katalog logów w repozytorium.
- **serialized_index/.gitkeep** – placeholder na zserializowane indeksy.
- **.github/workflows/ci.yml** – konfiguracja GitHub Actions uruchamiająca lint, mypy i testy w wielu wersjach Pythona.
