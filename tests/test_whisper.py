import sys
from unittest.mock import MagicMock

import pytest

from hns.cli import WhisperTranscriber


def _new():
    """Create a WhisperTranscriber without calling __init__, skipping model loading."""
    return WhisperTranscriber.__new__(WhisperTranscriber)


class TestGetModelName:
    def test_valid_model(self):
        assert _new()._get_model_name("small") == "small"

    def test_all_valid_models_accepted(self):
        t = _new()
        for model in WhisperTranscriber.VALID_MODELS:
            assert t._get_model_name(model) == model

    def test_invalid_model_falls_back_to_base(self):
        assert _new()._get_model_name("not-a-real-model") == "base"

    def test_env_var_used_when_no_arg(self, monkeypatch):
        monkeypatch.setenv("HNS_WHISPER_MODEL", "turbo")
        assert _new()._get_model_name(None) == "turbo"

    def test_arg_takes_precedence_over_env(self, monkeypatch):
        monkeypatch.setenv("HNS_WHISPER_MODEL", "turbo")
        assert _new()._get_model_name("small") == "small"

    def test_default_is_base_when_no_env(self, monkeypatch):
        monkeypatch.delenv("HNS_WHISPER_MODEL", raising=False)
        assert _new()._get_model_name(None) == "base"


class TestResolveDevice:
    @pytest.fixture
    def mock_ct2(self, monkeypatch):
        ct2 = MagicMock()
        monkeypatch.setitem(sys.modules, "ctranslate2", ct2)
        return ct2

    def test_auto_no_cuda_returns_cpu(self, mock_ct2, monkeypatch):
        monkeypatch.delenv("HNS_DEVICE", raising=False)
        mock_ct2.get_supported_compute_types.return_value = ["int8"]
        device, compute_type = _new()._resolve_device(None)
        assert device == "cpu"
        assert compute_type == "int8"

    def test_auto_with_cuda_returns_cuda_float16(self, mock_ct2, monkeypatch):
        monkeypatch.delenv("HNS_DEVICE", raising=False)
        mock_ct2.get_supported_compute_types.return_value = ["float16", "int8"]
        device, compute_type = _new()._resolve_device(None)
        assert device == "cuda"
        assert compute_type == "float16"

    def test_explicit_cpu(self, mock_ct2):
        device, compute_type = _new()._resolve_device("cpu")
        assert device == "cpu"
        assert compute_type == "int8"

    def test_explicit_cuda(self, mock_ct2):
        device, compute_type = _new()._resolve_device("cuda")
        assert device == "cuda"
        assert compute_type == "float16"

    def test_env_device_overrides_auto(self, mock_ct2, monkeypatch):
        monkeypatch.setenv("HNS_DEVICE", "cpu")
        mock_ct2.get_supported_compute_types.return_value = ["int8"]
        device, compute_type = _new()._resolve_device(None)
        assert device == "cpu"
        assert compute_type == "int8"
