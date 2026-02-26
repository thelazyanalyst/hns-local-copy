import sys
from unittest.mock import MagicMock

import pytest

from hns.cli import ParakeetTranscriber


def _new():
    """Create a ParakeetTranscriber without calling __init__, skipping model loading."""
    return ParakeetTranscriber.__new__(ParakeetTranscriber)


class TestGetModelName:
    def test_valid_model(self):
        assert _new()._get_model_name("nemo-parakeet-ctc-0.6b") == "nemo-parakeet-ctc-0.6b"

    def test_all_valid_models_accepted(self):
        t = _new()
        for model in ParakeetTranscriber.VALID_MODELS:
            assert t._get_model_name(model) == model

    def test_invalid_model_falls_back_to_default(self):
        assert _new()._get_model_name("not-a-model") == ParakeetTranscriber.DEFAULT_MODEL

    def test_env_var_used_when_no_arg(self, monkeypatch):
        monkeypatch.setenv("HNS_MODEL", "nemo-parakeet-ctc-1.1b")
        assert _new()._get_model_name(None) == "nemo-parakeet-ctc-1.1b"

    def test_default_when_no_arg_no_env(self, monkeypatch):
        monkeypatch.delenv("HNS_MODEL", raising=False)
        assert _new()._get_model_name(None) == ParakeetTranscriber.DEFAULT_MODEL


class TestResolveDevice:
    @pytest.fixture
    def mock_ort(self, monkeypatch):
        ort = MagicMock()
        monkeypatch.setitem(sys.modules, "onnxruntime", ort)
        return ort

    def test_auto_no_cuda_returns_cpu(self, mock_ort, monkeypatch):
        monkeypatch.delenv("HNS_DEVICE", raising=False)
        mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]
        assert _new()._resolve_device(None) == "cpu"

    def test_auto_with_cuda_returns_cuda(self, mock_ort, monkeypatch):
        monkeypatch.delenv("HNS_DEVICE", raising=False)
        mock_ort.get_available_providers.return_value = ["CUDAExecutionProvider", "CPUExecutionProvider"]
        assert _new()._resolve_device(None) == "cuda"

    def test_explicit_cpu(self):
        assert _new()._resolve_device("cpu") == "cpu"

    def test_explicit_cuda(self):
        assert _new()._resolve_device("cuda") == "cuda"

    def test_unknown_device_falls_back_to_cpu(self):
        assert _new()._resolve_device("tpu") == "cpu"

    def test_env_device_overrides_auto(self, mock_ort, monkeypatch):
        monkeypatch.setenv("HNS_DEVICE", "cuda")
        mock_ort.get_available_providers.return_value = ["CPUExecutionProvider"]
        assert _new()._resolve_device(None) == "cuda"
