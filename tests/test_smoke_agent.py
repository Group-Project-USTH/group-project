"""Real end-to-end run against the configured LLM (and Langfuse, if keys are set).

Excluded by default. Run with: uv run pytest -m integration --no-cov
"""

import shutil
from pathlib import Path

import pytest

from maintain_eval.config import get_settings
from maintain_eval.observability import new_run_id
from maintain_eval.schemas import Characteristic, Finding
from maintain_eval.version_b import run_smoke

SAMPLE = Path(__file__).parent / "fixtures" / "sample_project"

pytestmark = pytest.mark.integration


def test_agent_smoke_returns_cited_finding(tmp_path: Path) -> None:
    settings = get_settings()
    if not (settings.llm_model and settings.openai_api_key):
        pytest.skip("LLM_MODEL / OPENAI_API_KEY not configured")

    project = Path(shutil.copytree(SAMPLE, tmp_path / "sample_project"))
    before = {p.name: p.read_text() for p in project.iterdir()}

    finding = run_smoke(project, Characteristic.MODULARITY, run_id=f"it-{new_run_id()}")

    assert isinstance(finding, Finding)
    assert finding.source == "agent"
    for ev in finding.evidence:
        assert (project / ev.file).is_file(), f"cited file does not exist: {ev.file}"
    assert {p.name: p.read_text() for p in project.iterdir()} == before
