from pathlib import Path

import pytest
from fake_claude import FakeClaude
from upstream_repository import Upstream


@pytest.fixture
def upstream(tmp_path: Path) -> Upstream:
    return Upstream(tmp_path / "upstream")


@pytest.fixture
def fake_claude(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> FakeClaude:
    folder = tmp_path / "fake"
    folder.mkdir()
    return FakeClaude(folder, monkeypatch)
