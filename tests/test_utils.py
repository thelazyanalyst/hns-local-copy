import sys
from pathlib import Path

from hns.cli import _write_config, format_duration, get_default_save_dir, load_config


class TestFormatDuration:
    def test_zero(self):
        assert format_duration(0) == "00:00"

    def test_under_60(self):
        assert format_duration(59) == "00:59"

    def test_exact_60(self):
        assert format_duration(60) == "01:00"

    def test_3600(self):
        assert format_duration(3600) == "1:00:00"

    def test_3661(self):
        assert format_duration(3661) == "1:01:01"


class TestGetDefaultSaveDir:
    def test_linux(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "platform", "linux")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        assert get_default_save_dir() == tmp_path / ".local" / "share" / "hns" / "recordings"

    def test_darwin(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "platform", "darwin")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        assert get_default_save_dir() == tmp_path / "Library" / "Application Support" / "hns" / "recordings"

    def test_windows(self, monkeypatch, tmp_path):
        monkeypatch.setattr(sys, "platform", "win32")
        monkeypatch.setattr(Path, "home", lambda: tmp_path)
        assert get_default_save_dir() == tmp_path / "AppData" / "Roaming" / "hns" / "Recordings"


class TestLoadConfig:
    def test_missing_file_returns_empty(self, mock_home):
        assert load_config() == {}

    def test_valid_toml(self, mock_home):
        config_dir = mock_home / ".config" / "hns"
        config_dir.mkdir(parents=True)
        (config_dir / "config.toml").write_text('backend = "parakeet"\nmodel = "small"\n')
        assert load_config() == {"backend": "parakeet", "model": "small"}

    def test_malformed_toml_returns_empty(self, mock_home):
        config_dir = mock_home / ".config" / "hns"
        config_dir.mkdir(parents=True)
        (config_dir / "config.toml").write_bytes(b"[invalid toml\x00")
        assert load_config() == {}


class TestWriteConfig:
    def test_round_trip(self, mock_home):
        _write_config(backend="parakeet", model=None, language=None, save_dir=None)
        assert load_config()["backend"] == "parakeet"

    def test_partial_update_merges(self, mock_home):
        _write_config(backend="whisper", model="small", language=None, save_dir=None)
        _write_config(backend=None, model="medium", language=None, save_dir=None)
        cfg = load_config()
        assert cfg["backend"] == "whisper"
        assert cfg["model"] == "medium"

    def test_all_fields_round_trip(self, mock_home):
        _write_config(backend="whisper", model="base", language="en", save_dir="/tmp/recs")
        cfg = load_config()
        assert cfg == {"backend": "whisper", "model": "base", "language": "en", "save_dir": "/tmp/recs"}

    def test_none_args_do_not_overwrite_existing(self, mock_home):
        _write_config(backend="parakeet", model="nemo-parakeet-ctc-0.6b", language=None, save_dir=None)
        _write_config(backend=None, model=None, language=None, save_dir=None)
        cfg = load_config()
        assert cfg["backend"] == "parakeet"
        assert cfg["model"] == "nemo-parakeet-ctc-0.6b"
