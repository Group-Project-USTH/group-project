import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from maintainability_agent.config import get_settings

_ENV_PREFIXES = ("LLM_", "OPENAI_", "LANGFUSE_")


@pytest.fixture(autouse=True)
def hermetic_settings(
    request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> Iterator[None]:
    """Unit tests never see real credentials from the shell or the repo's `.env`.

    `.env` is resolved relative to the working directory, so running from an empty
    tmp dir hides it. Integration tests opt out to use the developer's real config.
    """
    if request.node.get_closest_marker("integration") is None:
        for name in list(os.environ):
            if name.startswith(_ENV_PREFIXES):
                monkeypatch.delenv(name)
        monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()
