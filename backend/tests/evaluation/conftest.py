from pathlib import Path

import pytest
from upstream_repository import Upstream


@pytest.fixture
def upstream(tmp_path: Path) -> Upstream:
    return Upstream(tmp_path / "upstream")
