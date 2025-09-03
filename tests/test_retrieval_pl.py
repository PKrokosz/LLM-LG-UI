# smoke test – nie blokuje CI jeśli brak danych
import os, pytest

@pytest.mark.smoke
def test_repo_exists():
    assert os.path.exists("settings.yaml")
