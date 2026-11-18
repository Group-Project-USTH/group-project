import json
from pathlib import Path

import pytest
from fake_claude import FakeClaude, finding, success

from maintainability_lens.evaluation import ApproachError, decide_with_claude_code
from maintainability_lens.schemas import Characteristic, Verdict


@pytest.fixture
def checkout(tmp_path: Path) -> Path:
    folder = tmp_path / "checkout"
    folder.mkdir()
    return folder


def test_findings_and_cost_come_from_the_structured_output(
    tmp_path: Path, fake_claude: FakeClaude, checkout: Path
) -> None:
    fake_claude.answer(success([finding(characteristic) for characteristic in Characteristic]))

    file_findings = decide_with_claude_code(fake_claude.options(tmp_path), checkout, "app.py")

    assert [entry.characteristic for entry in file_findings.findings] == list(Characteristic)
    assert {entry.verdict for entry in file_findings.findings} == {Verdict.FAIL}
    assert file_findings.cost_usd == 0.42
    assert file_findings.model == "claude-sonnet-5-5"


def test_claude_runs_in_the_checkout_and_asks_about_the_file_with_the_skill(
    tmp_path: Path, fake_claude: FakeClaude, checkout: Path
) -> None:
    fake_claude.answer(success([finding(characteristic) for characteristic in Characteristic]))

    decide_with_claude_code(fake_claude.options(tmp_path), checkout, "pkg/app.py")

    prompt = fake_claude.call()["argv"][fake_claude.call()["argv"].index("-p") + 1]
    assert fake_claude.call()["cwd"] == str(checkout)
    assert "pkg/app.py" in prompt
    assert "/maintainability-lens:evaluate" in prompt
    assert fake_claude.option("--model") == "claude-sonnet-5-5"
    assert fake_claude.option("--max-budget-usd") == "1.5"
    assert fake_claude.option("--plugin-dir") == str(tmp_path)


def test_claude_sees_only_the_plugin_server_and_read_only_tools(
    tmp_path: Path, fake_claude: FakeClaude, checkout: Path
) -> None:
    fake_claude.answer(success([finding(characteristic) for characteristic in Characteristic]))

    decide_with_claude_code(fake_claude.options(tmp_path), checkout, "app.py")

    assert "--strict-mcp-config" in fake_claude.call()["argv"]
    assert fake_claude.option("--setting-sources") == "project,local"
    assert set(fake_claude.option("--tools").split(",")) <= {
        "Read",
        "Grep",
        "Glob",
        "Skill",
        "ToolSearch",
    }
    servers = json.loads(fake_claude.mcp_file.read_text())["mcpServers"]
    assert list(servers) == ["maintainability-lens"]
    assert str(tmp_path / "backend") in servers["maintainability-lens"]["args"]


def test_an_error_result_is_an_approach_error(
    tmp_path: Path, fake_claude: FakeClaude, checkout: Path
) -> None:
    fake_claude.answer({"type": "result", "subtype": "error_max_budget_usd", "is_error": True})

    with pytest.raises(ApproachError, match="error_max_budget_usd"):
        decide_with_claude_code(fake_claude.options(tmp_path), checkout, "app.py")


def test_an_answer_without_every_characteristic_is_an_approach_error(
    tmp_path: Path, fake_claude: FakeClaude, checkout: Path
) -> None:
    fake_claude.answer(success([finding(Characteristic.MODULARITY)]))

    with pytest.raises(ApproachError, match="testability"):
        decide_with_claude_code(fake_claude.options(tmp_path), checkout, "app.py")


def test_a_pass_without_evidence_is_an_approach_error(
    tmp_path: Path, fake_claude: FakeClaude, checkout: Path
) -> None:
    findings = [finding(characteristic) for characteristic in Characteristic]
    findings[0] = {**findings[0], "verdict": "pass", "evidence": []}
    fake_claude.answer(success(findings))

    with pytest.raises(ApproachError):
        decide_with_claude_code(fake_claude.options(tmp_path), checkout, "app.py")
