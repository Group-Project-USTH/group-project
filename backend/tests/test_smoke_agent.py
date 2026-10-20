"""Real end-to-end run against the configured LLM (and Langfuse, if keys are set).

Excluded by default. Run with: uv run pytest -m integration --no-cov
Traces (if Langfuse keys are set) land in the `test` environment.
"""

import shutil
from pathlib import Path

import pytest

from maintainability_agent.agent import run_smoke
from maintainability_agent.config import get_settings
from maintainability_agent.observability import new_run_id
from maintainability_agent.schemas import Characteristic, Finding

SAMPLE = Path(__file__).parent / "fixtures" / "sample_project"

pytestmark = pytest.mark.integration


def test_agent_smoke_returns_cited_finding(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Keep test traces out of development/experiment data in Langfuse.
    monkeypatch.setenv("LANGFUSE_TRACING_ENVIRONMENT", "test")
    get_settings.cache_clear()
    settings = get_settings()
    if not (settings.llm_model and settings.openai_api_key):
        pytest.skip("LLM_MODEL / OPENAI_API_KEY not configured")

    project = Path(shutil.copytree(SAMPLE, tmp_path / "sample_project"))
    before = {p.name: p.read_text() for p in project.iterdir()}

    finding = run_smoke(project, Characteristic.MODULARITY, run_id=f"it-{new_run_id()}")

    assert isinstance(finding, Finding)
    for ev in finding.evidence:
        assert (project / ev.file).is_file(), f"cited file does not exist: {ev.file}"
    assert {p.name: p.read_text() for p in project.iterdir()} == before
