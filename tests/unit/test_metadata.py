from __future__ import annotations

from tfm_pipeline.config import ExperimentConfig
from tfm_pipeline.metadata import build_metadata


class TestBuildMetadata:
    def test_libraries_nested_versions(self) -> None:
        config = ExperimentConfig()
        meta = build_metadata(config)
        libs = meta["libraries"]
        assert "pandas" in libs
        assert "numpy" in libs
        assert "torch" in libs
        # Each library entry must be a dict, not a bare string
        assert isinstance(libs["pandas"], dict)
        assert isinstance(libs["numpy"], dict)
        assert isinstance(libs["torch"], dict)
        # No top-level "version" key inside libraries (old collision bug)
        assert "version" not in libs
        # pandas dict should contain version
        assert "version" in libs["pandas"]

    def test_config_snapshot(self) -> None:
        config = ExperimentConfig(assets=("AAPL", "MSFT"), window_size=60)
        meta = build_metadata(config)
        assert meta["config"]["assets"] == ("AAPL", "MSFT")
        assert meta["config"]["window_size"] == 60

    def test_extra_merged(self) -> None:
        config = ExperimentConfig()
        meta = build_metadata(config, extra={"runner": "test"})
        assert meta["extra"]["runner"] == "test"
