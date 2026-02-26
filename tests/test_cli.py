from unittest.mock import patch

from click.testing import CliRunner

from hns.cli import ParakeetTranscriber, WhisperTranscriber, main


class TestListModels:
    def test_whisper_list_models_exits_ok(self, mock_home):
        runner = CliRunner()
        result = runner.invoke(main, ["--list-models"])
        assert result.exit_code == 0

    def test_parakeet_list_models_exits_ok(self, mock_home):
        runner = CliRunner()
        result = runner.invoke(main, ["--backend", "parakeet", "--list-models"])
        assert result.exit_code == 0


class TestBackendResolution:
    """Backend resolves in priority order: CLI flag > env var > config file > default (whisper)."""

    def test_default_is_whisper(self, mock_home, monkeypatch):
        monkeypatch.delenv("HNS_BACKEND", raising=False)
        runner = CliRunner()
        with patch.object(WhisperTranscriber, "list_models") as mock_list:
            runner.invoke(main, ["--list-models"])
        assert mock_list.called

    def test_cli_flag_selects_parakeet(self, mock_home, monkeypatch):
        monkeypatch.delenv("HNS_BACKEND", raising=False)
        runner = CliRunner()
        with patch.object(ParakeetTranscriber, "list_models") as mock_list:
            runner.invoke(main, ["--backend", "parakeet", "--list-models"])
        assert mock_list.called

    def test_env_var_selects_parakeet(self, mock_home, monkeypatch):
        monkeypatch.setenv("HNS_BACKEND", "parakeet")
        runner = CliRunner()
        with patch.object(ParakeetTranscriber, "list_models") as mock_list:
            runner.invoke(main, ["--list-models"])
        assert mock_list.called

    def test_config_selects_parakeet(self, mock_home, monkeypatch):
        monkeypatch.delenv("HNS_BACKEND", raising=False)
        config_dir = mock_home / ".config" / "hns"
        config_dir.mkdir(parents=True)
        (config_dir / "config.toml").write_text('backend = "parakeet"\n')
        runner = CliRunner()
        with patch.object(ParakeetTranscriber, "list_models") as mock_list:
            runner.invoke(main, ["--list-models"])
        assert mock_list.called

    def test_cli_flag_overrides_env(self, mock_home, monkeypatch):
        monkeypatch.setenv("HNS_BACKEND", "parakeet")
        runner = CliRunner()
        with patch.object(WhisperTranscriber, "list_models") as mock_list:
            runner.invoke(main, ["--backend", "whisper", "--list-models"])
        assert mock_list.called


class TestLastFlag:
    def test_missing_recording_exits_with_error(self, mock_home):
        runner = CliRunner()
        with patch("hns.cli.WhisperTranscriber"):
            result = runner.invoke(main, ["--last"])
        assert result.exit_code == 1
