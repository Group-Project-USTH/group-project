"""Langfuse tracing for evaluation runs, degrading to a no-op when not configured.

Usage:

    with traced_run(run_id=run_id, characteristic=c, input={...}) as run:
        result = agent.invoke(inputs, config=run.config)
        run.set_output(finding)

Each run is one trace whose root is an `agent` observation named `evaluate-characteristic`,
with the run's input/output, `run_id`/`characteristic` as metadata, `characteristic` as a tag, the
environment and release, and an optional session grouping repeated runs. LangChain/LangGraph
observations (generations, tool calls) nest under the root via the callback handler.
The SDK flushes buffered spans on interpreter exit.
"""

import logging
import re
import subprocess
import uuid
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING, Any

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.runnables import RunnableConfig

from maintain_eval.config import Settings, get_settings
from maintain_eval.schemas import Characteristic

if TYPE_CHECKING:
    from langfuse import Langfuse
    from opentelemetry.sdk.trace import ReadableSpan

logger = logging.getLogger(__name__)

# Names are an API for dashboards and evaluators: stable, verb-first, no dynamic values.
TRACE_NAME = "evaluate-characteristic"

# LangChain middleware hooks that ran without producing anything (e.g.
# `PatchToolCallsMiddleware.before_agent`). The callback handler types them as `agent`,
# which clutters the trace and the agent graph. They never have children.
_EMPTY_HOOK_NAME = re.compile(r"Middleware\.(before|after)_(agent|model)$")

_client_initialised = False


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


@cache
def _git_release() -> str | None:
    """Commit of this code, with `-dirty` if the working tree has uncommitted changes."""
    try:
        out = subprocess.run(
            ["git", "describe", "--always", "--dirty", "--abbrev=12"],
            cwd=Path(__file__).parent,
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return out.stdout.strip() or None


def should_export_span(span: "ReadableSpan") -> bool:
    """Langfuse's default export filter, minus empty middleware hook spans."""
    from langfuse.span_filter import is_default_export_span

    if not is_default_export_span(span):
        return False
    attrs = span.attributes or {}
    is_empty_hook = bool(_EMPTY_HOOK_NAME.search(span.name)) and (
        "langfuse.observation.output" not in attrs
    )
    return not is_empty_hook


def build_langfuse_client(settings: Settings, **overrides: Any) -> "Langfuse":
    """Langfuse client with this project's environment, release, masking and span filter."""
    from langfuse import Langfuse

    from maintain_eval.masking import mask_otel_spans

    assert settings.langfuse_secret_key is not None
    kwargs: dict[str, Any] = {
        "public_key": settings.langfuse_public_key,
        "secret_key": settings.langfuse_secret_key.get_secret_value(),
        "base_url": settings.langfuse_base_url,
        "environment": settings.langfuse_tracing_environment,
        "release": settings.langfuse_release or _git_release(),
        "mask_otel_spans": mask_otel_spans,
        "should_export_span": should_export_span,
    }
    return Langfuse(**(kwargs | overrides))


def _init_langfuse(settings: Settings) -> bool:
    """Create the Langfuse singleton once from settings. Returns False on failure."""
    global _client_initialised
    if _client_initialised:
        return True
    try:
        build_langfuse_client(settings)
    except Exception:
        logger.warning("Langfuse initialisation failed; tracing disabled.", exc_info=True)
        return False
    _client_initialised = True
    return True


def _tracing_ready(settings: Settings) -> bool:
    if not settings.langfuse_enabled:
        logger.info("Langfuse disabled via LANGFUSE_ENABLED=false.")
        return False
    if not settings.langfuse_configured:
        logger.warning(
            "Langfuse keys missing (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY); "
            "running without tracing."
        )
        return False
    return _init_langfuse(settings)


def check_langfuse_auth(settings: Settings | None = None) -> bool | None:
    """Blocking credential check for CLI use. None if tracing is not configured."""
    settings = settings or get_settings()
    if not _tracing_ready(settings):
        return None
    from langfuse import get_client

    ok = get_client(public_key=settings.langfuse_public_key).auth_check()
    if not ok:
        logger.warning("Langfuse rejected the credentials; traces will not be stored.")
    return ok


def _trace_url(client: "Langfuse") -> str | None:
    # Looks up the project id over the network once per process; tracing must never
    # break a run, so failures just mean no URL.
    try:
        return client.get_trace_url()
    except Exception:
        logger.warning("Could not resolve the Langfuse trace URL.", exc_info=True)
        return None


@dataclass
class TracedRun:
    """Handle for one traced run. All methods are no-ops when tracing is off."""

    config: RunnableConfig
    trace_url: str | None = None
    _root: Any = field(default=None, repr=False)

    def set_output(self, output: Any) -> None:
        if self._root is not None:
            self._root.update(output=output)

    def fail(self, message: str) -> None:
        if self._root is not None:
            self._root.update(level="ERROR", status_message=message)


@contextmanager
def traced_run(
    *,
    run_id: str,
    characteristic: Characteristic,
    input: Any = None,
    session_id: str | None = None,
    component_version: str | None = None,
    tags: Sequence[str] = (),
    settings: Settings | None = None,
) -> Iterator[TracedRun]:
    """Trace one evaluation run to Langfuse if configured.

    `session_id` groups related traces, e.g. repeated runs of the same evaluation.
    `component_version` is the Langfuse `version` field (e.g. the agent prompt version).
    Exceptions raised inside the block mark the root observation as ERROR and propagate.
    """
    settings = settings or get_settings()
    metadata = {"run_id": run_id, "characteristic": characteristic.value}
    all_tags = [f"characteristic:{characteristic.value}", *tags]

    if not _tracing_ready(settings):
        yield TracedRun(config=RunnableConfig(callbacks=[], metadata=dict(metadata), tags=all_tags))
        return

    from langfuse import get_client, propagate_attributes
    from langfuse.langchain import CallbackHandler

    client = get_client(public_key=settings.langfuse_public_key)
    callbacks: list[BaseCallbackHandler] = [
        CallbackHandler(public_key=settings.langfuse_public_key)
    ]
    config = RunnableConfig(callbacks=callbacks, metadata=dict(metadata), tags=all_tags)

    with (
        propagate_attributes(
            session_id=session_id,
            metadata=metadata,
            tags=all_tags,
            trace_name=TRACE_NAME,
            version=component_version,
        ),
        client.start_as_current_observation(
            as_type="agent", name=TRACE_NAME, input=input, version=component_version
        ) as root,
    ):
        run = TracedRun(config=config, trace_url=_trace_url(client), _root=root)
        try:
            yield run
        except Exception as exc:
            run.fail(f"{type(exc).__name__}: {exc}")
            raise
