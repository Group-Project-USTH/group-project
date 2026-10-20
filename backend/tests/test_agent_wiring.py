"""Offline tests of the agent wiring, using a scripted fake chat model (no LLM, no keys)."""

import json
import shutil
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
from langchain_core.language_models import BaseChatModel
from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, ToolMessage

from maintain_eval.agent import AgentOutputError, build_agent, run_smoke
from maintain_eval.schemas import Characteristic, Evidence, Verdict

SAMPLE = Path(__file__).parent / "fixtures" / "sample_project"


class ScriptedChatModel(GenericFakeChatModel):
    """Replays fixed AI messages; accepts (and ignores) bound tools."""

    def bind_tools(self, tools: Sequence[Any], **kwargs: Any) -> "ScriptedChatModel":  # type: ignore[override]
        return self


def scripted(*messages: AIMessage) -> BaseChatModel:
    return ScriptedChatModel(messages=iter(messages))


def call(name: str, args: dict[str, Any], call_id: str) -> dict[str, Any]:
    return {"name": name, "args": args, "id": call_id, "type": "tool_call"}


def answer(payload: dict[str, Any]) -> AIMessage:
    """Final message in the native structured-output (JSON text) format."""
    return AIMessage(content=json.dumps(payload))


ANSWER_FAIL = answer(
    {
        "verdict": "fail",
        "evidence": [{"file": "/app.py", "line_start": 6, "line_end": 25}],
        "rationale": "process_order mixes validation, pricing, I/O and output.",
    }
)


@pytest.fixture
def project(tmp_path: Path) -> Path:
    return Path(shutil.copytree(SAMPLE, tmp_path / "sample_project"))


def snapshot(root: Path) -> dict[str, str]:
    return {str(p.relative_to(root)): p.read_text() for p in sorted(root.rglob("*")) if p.is_file()}


def test_agent_cannot_modify_target(project: Path) -> None:
    before = snapshot(project)
    model = scripted(
        AIMessage(
            content="",
            tool_calls=[
                call("write_file", {"file_path": "/pwned.py", "content": "x"}, "w"),
                call(
                    "edit_file",
                    {"file_path": "/app.py", "old_string": "def", "new_string": "XX"},
                    "e",
                ),
            ],
        ),
        ANSWER_FAIL,
    )
    result = build_agent(project, model).invoke({"messages": [{"role": "user", "content": "go"}]})

    tool_errors = {m.name: str(m.content) for m in result["messages"] if isinstance(m, ToolMessage)}
    assert "permission denied" in tool_errors["write_file"].lower()
    assert "permission denied" in tool_errors["edit_file"].lower()
    assert snapshot(project) == before


def test_run_smoke_returns_validated_finding(project: Path) -> None:
    model = scripted(
        AIMessage(content="", tool_calls=[call("read_file", {"file_path": "/app.py"}, "r")]),
        ANSWER_FAIL,
    )
    finding = run_smoke(project, Characteristic.MODULARITY, run_id="t1", model=model)
    assert finding.characteristic is Characteristic.MODULARITY
    assert finding.verdict is Verdict.FAIL
    assert finding.evidence == [Evidence(file="app.py", line_start=6, line_end=25)]


@pytest.mark.parametrize(
    "final",
    [
        AIMessage(content="I think it fails."),  # prose instead of JSON
        answer({"verdict": "maybe", "rationale": "?"}),  # not a valid Verdict
        answer({"verdict": "pass", "rationale": "ok"}),  # PASS without evidence -> Finding rejects
    ],
    ids=["prose", "invalid-verdict", "pass-without-evidence"],
)
def test_run_smoke_rejects_bad_answers(project: Path, final: AIMessage) -> None:
    with pytest.raises(AgentOutputError):
        run_smoke(project, Characteristic.TESTABILITY, run_id="t2", model=scripted(final))


def test_build_agent_requires_existing_directory(tmp_path: Path) -> None:
    with pytest.raises(NotADirectoryError):
        build_agent(tmp_path / "missing", scripted())


def test_build_model_names_llm_calls_by_operation() -> None:
    from maintain_eval.agent.deep_agent import LLM_CALL_NAME, build_model
    from maintain_eval.config import Settings

    model = build_model(Settings(llm_model="openai:some-model", openai_api_key="sk-test"))
    assert model.get_name() == LLM_CALL_NAME
