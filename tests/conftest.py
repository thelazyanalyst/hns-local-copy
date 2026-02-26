from pathlib import Path

import pytest


@pytest.fixture
def mock_home(tmp_path, monkeypatch):
    """Redirect Path.home() to a temporary directory for config isolation."""
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    return tmp_path
