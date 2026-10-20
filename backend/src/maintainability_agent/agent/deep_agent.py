"""A DeepAgents agent that judges one characteristic with read-only file access.

This is wiring only: the prompt is deliberately minimal and not tuned.
"""

from collections.abc import Callable
from pathlib import Path
from typing import Any

from deepagents import FilesystemPermission, create_deep_agent
from langchain.agents.structured_output import ProviderStrategy, StructuredOutputError
from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel
from pydantic import BaseModel, Field, ValidationError

from maintainability_agent.agent.read_only_filesystem_backend import ReadOnlyFilesystemBackend
from maintainability_agent.config import Settings, get_settings
from maintainability_agent.observability import traced_run
from maintainability_agent.schemas import Characteristic, Evidence, Finding, Verdict

# Bump whenever SYSTEM_PROMPT or the agent's tools/output schema change. Sent to Langfuse
# as the observation `version`, so runs of different prompt iterations can be compared.
PROMPT_VERSION = "1.0"
# Observation name for every LLM call in the agent loop (traces name the operation,
# not the model class; the model id is recorded separately on each generation).
LLM_CALL_NAME = "decide-next-action"

SYSTEM_PROMPT = """\
You evaluate the maintainability of a software project (ISO/IEC 25010).
You will be asked about exactly one sub-characteristic. Inspect the project files
with your read-only file tools, then answer PASS, FAIL or UNKNOWN.
For PASS or FAIL you MUST cite at least one file path and line number that
supports your answer. Answer UNKNOWN if you cannot decide from the code.
"""

# Deny every mutating file tool (write_file, edit_file, delete) on every path.
# ReadOnlyFilesystemBackend enforces the same thing at the backend layer.
READ_ONLY_PERMISSIONS = [FilesystemPermission(operations=["write"], paths=["/**"], mode="deny")]


class AgentOutputError(RuntimeError):
    """The agent finished without a valid structured answer."""


class AgentAnswer(BaseModel):
    """Structured output the agent must return."""

    verdict: Verdict
    evidence: list[Evidence] = Field(
        default_factory=list,
        description="File (relative to project root) and line(s) backing the verdict.",
    )
    rationale: str = Field(description="One or two sentences explaining the verdict.")


def build_model(settings: Settings) -> BaseChatModel:
    if not settings.llm_model:
        raise AgentOutputError("LLM_MODEL is not set (expected `provider:model`).")
    kwargs: dict[str, Any] = {"name": LLM_CALL_NAME}
    if settings.openai_api_key is not None:
        kwargs["api_key"] = settings.openai_api_key.get_secret_value()
    if settings.openai_base_url:
        kwargs["base_url"] = settings.openai_base_url
    if settings.llm_model.startswith("openai:"):
        # Same default as deepagents' OpenAI profile. Some OpenAI-compatible routers
        # silently ignore `tool_choice` on /chat/completions but honour it on /responses.
        kwargs["use_responses_api"] = True
    model: BaseChatModel = init_chat_model(settings.llm_model, **kwargs)
    return model


def build_agent(target: Path, model: BaseChatModel) -> Any:
    """Create a DeepAgent that can read, but not modify, files under `target`."""
    target = target.resolve()
    if not target.is_dir():
        raise NotADirectoryError(target)
    return create_deep_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        backend=ReadOnlyFilesystemBackend(root_dir=target, virtual_mode=True),
        permissions=READ_ONLY_PERMISSIONS,
        # Native JSON-schema output. ToolStrategy relies on a forced `tool_choice`, which
        # some OpenAI-compatible routers drop (the model then ends with no answer at all).
        response_format=ProviderStrategy(AgentAnswer),
    )


def to_finding(answer: AgentAnswer, characteristic: Characteristic) -> Finding:
    # The agent sees virtual paths ("/app.py"); store them relative to the project root.
    evidence = [e.model_copy(update={"file": e.file.lstrip("/")}) for e in answer.evidence]
    return Finding(
        characteristic=characteristic,
        verdict=answer.verdict,
        evidence=evidence,
        rationale=answer.rationale,
    )


def _finding_from_result(result: dict[str, Any], characteristic: Characteristic) -> Finding:
    answer = result.get("structured_response")
    if not isinstance(answer, AgentAnswer):
        raise AgentOutputError(
            f"Agent returned no structured answer (got {type(answer).__name__})."
        )
    try:
        return to_finding(answer, characteristic)
    except ValidationError as exc:
        raise AgentOutputError(f"Agent answer failed validation: {exc}") from exc


def evaluate_characteristic(
    target: Path,
    characteristic: Characteristic,
    run_id: str,
    settings: Settings | None = None,
    model: BaseChatModel | None = None,
    session_id: str | None = None,
    on_trace_url: Callable[[str], None] | None = None,
) -> Finding:
    """Ask the agent about one characteristic of `target` and return a validated Finding.

    `on_trace_url` is called with the Langfuse trace URL before the agent starts, if tracing.
    """
    agent = build_agent(target, model or build_model(settings or get_settings()))
    question = (
        f"Evaluate the {characteristic.value} of the project at `/`. "
        "Answer PASS, FAIL or UNKNOWN and cite file + line."
    )
    with traced_run(
        run_id=run_id,
        characteristic=characteristic,
        input={"target": str(target), "characteristic": characteristic.value, "question": question},
        session_id=session_id,
        component_version=PROMPT_VERSION,
    ) as run:
        if run.trace_url and on_trace_url:
            on_trace_url(run.trace_url)
        config = run.config | {"recursion_limit": 60}
        try:
            result = agent.invoke(
                {"messages": [{"role": "user", "content": question}]}, config=config
            )
        except StructuredOutputError as exc:
            raise AgentOutputError(f"Agent answer could not be parsed: {exc}") from exc
        finding = _finding_from_result(result, characteristic)
        run.set_output(finding.model_dump(mode="json"))
    return finding
