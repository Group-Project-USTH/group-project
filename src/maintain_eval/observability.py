"""Langfuse tracing for agent runs, degrading to a no-op when not configured.

Usage:

    with traced_run(version="B", run_id=run_id, characteristic=c) as config:
        agent.invoke(inputs, config=config)

Every trace gets `version`, `run_id` and `characteristic` as metadata and tags,
and `run_id` as the Langfuse session id, so repeated runs can be grouped/filtered.
"""

import atexit
import logging
import uuid
from collections.abc import Iterator, Sequence
from contextlib import contextmanager
from typing import Literal

from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.runnables import RunnableConfig

from maintain_eval.config import Settings, get_settings
from maintain_eval.schemas import Characteristic

logger = logging.getLogger(__name__)

PipelineVersion = Literal["A", "B"]
TRACE_NAME = "maintain-eval"

_client_initialised = False


def new_run_id() -> str:
    return uuid.uuid4().hex[:12]


def _init_langfuse(settings: Settings) -> bool:
    """Create the Langfuse singleton once from settings. Returns False on failure."""
    global _client_initialised
    if _client_initialised:
        return True
    try:
        from langfuse import Langfuse

        assert settings.langfuse_secret_key is not None  # guaranteed by langfuse_configured
        client = Langfuse(
            public_key=settings.langfuse_public_key,
            secret_key=settings.langfuse_secret_key.get_secret_value(),
            base_url=settings.langfuse_base_url,
        )
    except Exception:
        logger.warning("Langfuse initialisation failed; tracing disabled.", exc_info=True)
        return False
    atexit.register(client.shutdown)  # flush buffered spans before the process exits
    _client_initialised = True
    return True


def _callbacks(settings: Settings) -> list[BaseCallbackHandler]:
    if not settings.langfuse_enabled:
        logger.info("Langfuse disabled via LANGFUSE_ENABLED=false.")
        return []
    if not settings.langfuse_configured:
        logger.warning(
            "Langfuse keys missing (LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY); "
            "running without tracing."
        )
        return []
    if not _init_langfuse(settings):
        return []
    from langfuse.langchain import CallbackHandler

    return [CallbackHandler(public_key=settings.langfuse_public_key)]


@contextmanager
def traced_run(
    *,
    version: PipelineVersion,
    run_id: str,
    characteristic: Characteristic,
    tags: Sequence[str] = (),
    settings: Settings | None = None,
) -> Iterator[RunnableConfig]:
    """Yield a LangChain `RunnableConfig` that traces the run to Langfuse if configured."""
    settings = settings or get_settings()
    metadata = {"version": version, "run_id": run_id, "characteristic": characteristic.value}
    all_tags = [f"version:{version}", f"characteristic:{characteristic.value}", *tags]
    callbacks = _callbacks(settings)
    config = RunnableConfig(
        callbacks=callbacks, metadata=dict(metadata), tags=all_tags, run_name=TRACE_NAME
    )

    if not callbacks:
        yield config
        return

    from langfuse import propagate_attributes

    with propagate_attributes(
        session_id=run_id, metadata=metadata, tags=all_tags, trace_name=TRACE_NAME
    ):
        yield config
