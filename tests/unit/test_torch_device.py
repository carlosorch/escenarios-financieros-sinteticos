from __future__ import annotations

from unittest.mock import patch

import pytest

pytest.importorskip("torch")

from tfm_pipeline.models.vae import select_torch_device


class TestSelectTorchDevice:
    def test_explicit_device_wins(self) -> None:
        assert select_torch_device("cpu").type == "cpu"

    def test_prefers_cuda_when_available(self) -> None:
        with patch("torch.cuda.is_available", return_value=True), patch("torch.backends.mps.is_available", return_value=True):
            assert select_torch_device().type == "cuda"

    def test_uses_mps_when_cuda_unavailable(self) -> None:
        with patch("torch.cuda.is_available", return_value=False), patch("torch.backends.mps.is_available", return_value=True):
            assert select_torch_device().type == "mps"

    def test_falls_back_to_cpu(self) -> None:
        with patch("torch.cuda.is_available", return_value=False), patch("torch.backends.mps.is_available", return_value=False):
            assert select_torch_device().type == "cpu"
