from __future__ import annotations

from pathlib import Path

from tfm_pipeline.config import ExperimentConfig
from tfm_pipeline.metadata import _repo_root, build_metadata


class TestRepoRoot:
    def test_finds_parent_git_directory(self, tmp_path: Path) -> None:
        repo = tmp_path / "repo"
        nested = repo / "src" / "package"
        nested.mkdir(parents=True)
        (repo / ".git").mkdir()

        assert _repo_root(nested) == repo

    def test_returns_none_without_git_directory(self, tmp_path: Path) -> None:
        nested = tmp_path / "not_repo" / "src"
        nested.mkdir(parents=True)

        assert _repo_root(nested) is None


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
        if libs["torch"]:
            assert "mps_available" in libs["torch"]
            assert "mps_built" in libs["torch"]

    def test_config_snapshot(self) -> None:
        config = ExperimentConfig(assets=("AAPL", "MSFT"), window_size=60)
        meta = build_metadata(config)
        assert meta["config"]["assets"] == ("AAPL", "MSFT")
        assert meta["config"]["window_size"] == 60

    def test_extra_merged(self) -> None:
        config = ExperimentConfig()
        meta = build_metadata(config, extra={"runner": "test"})
        assert meta["extra"]["runner"] == "test"

    def test_git_metadata_populated_inside_repo(self) -> None:
        meta = build_metadata(ExperimentConfig())
        assert meta["git_revision"]
        assert meta["git_branch"]
