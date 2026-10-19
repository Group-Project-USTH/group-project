import json
import logging
import uuid
from collections.abc import Iterator

import pytest
from langchain_core.language_models.fake_chat_models import FakeListChatModel
from opentelemetry.sdk.trace import ReadableSpan
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

import maintain_eval.observability as obs
from maintain_eval.config import Settings
from maintain_eval.observability import new_run_id, traced_run
from maintain_eval.schemas import Characteristic


def test_no_keys_degrades_to_noop_with_warning(caplog: pytest.LogCaptureFixture) -> None:
    with (
        caplog.at_level(logging.WARNING),
        traced_run(version="B", run_id="r1", characteristic=Characteristic.MODULARITY) as run,
    ):
        assert run.config["callbacks"] == []
        assert run.trace_url is None
        run.set_output({"ignored": True})  # no-ops without tracing
        run.fail("ignored")
    assert "Langfuse keys missing" in caplog.text


def test_disabled_flag_degrades_without_warning(caplog: pytest.LogCaptureFixture) -> None:
    settings = Settings(langfuse_enabled=False, langfuse_public_key="pk", langfuse_secret_key="sk")
    with (
        caplog.at_level(logging.WARNING),
        traced_run(
            version="A",
            run_id="r2",
            characteristic=Characteristic.TESTABILITY,
            settings=settings,
        ) as run,
    ):
        assert run.config["callbacks"] == []
    assert caplog.text == ""


def test_untraced_config_still_carries_metadata_and_tags() -> None:
    with traced_run(
        version="B", run_id="abc", characteristic=Characteristic.ANALYSABILITY, tags=["smoke"]
    ) as run:
        assert run.config["metadata"] == {
            "version": "B",
            "run_id": "abc",
            "characteristic": "analysability",
        }
        assert run.config["tags"] == ["version:B", "characteristic:analysability", "smoke"]


def test_new_run_id_is_unique_and_short() -> None:
    ids = {new_run_id() for _ in range(100)}
    assert len(ids) == 100
    assert all(len(i) == 12 for i in ids)


@pytest.mark.parametrize("env", ["langfuse-prod", "Prod", "has space", "x" * 41])
def test_invalid_tracing_environment_is_rejected(env: str) -> None:
    with pytest.raises(ValueError):
        Settings(langfuse_tracing_environment=env)


# --- keyed path: real Langfuse client + in-memory exporter, no network --------------------


@pytest.fixture
def exporter(monkeypatch: pytest.MonkeyPatch) -> Iterator[tuple[InMemorySpanExporter, Settings]]:
    """Client built by our factory (env, release, masking, filter) exporting to memory."""
    public_key = f"pk-lf-test-{uuid.uuid4().hex}"  # the SDK keeps one client per key
    settings = Settings(
        langfuse_public_key=public_key,
        langfuse_secret_key="sk-lf-test",
        langfuse_base_url="http://127.0.0.1:9",
        langfuse_tracing_environment="test",
        langfuse_release="rel-123",
    )
    memory = InMemorySpanExporter()
    client = obs.build_langfuse_client(settings, span_exporter=memory)
    monkeypatch.setattr(obs, "_client_initialised", True)
    monkeypatch.setattr(obs, "_trace_url", lambda _client: "https://langfuse.test/trace/1")
    yield memory, settings
    client.shutdown()


def spans_by_name(memory: InMemorySpanExporter) -> dict[str, ReadableSpan]:
    return {s.name: s for s in memory.get_finished_spans()}


def attrs(span: ReadableSpan) -> dict[str, object]:
    return dict(span.attributes or {})


def test_keyed_run_has_agent_root_with_clean_io(
    exporter: tuple[InMemorySpanExporter, Settings],
) -> None:
    memory, settings = exporter
    with traced_run(
        version="B",
        run_id="run123",
        characteristic=Characteristic.MODULARITY,
        input={"target": "proj", "characteristic": "modularity"},
        session_id="stability-1",
        component_version="1.0",
        settings=settings,
    ) as run:
        assert run.trace_url == "https://langfuse.test/trace/1"
        assert len(run.config["callbacks"]) == 1
        FakeListChatModel(responses=["ok"]).invoke("hi", config=run.config)
        run.set_output({"verdict": "fail"})
    obs.build_langfuse_client(settings).flush()

    spans = spans_by_name(memory)
    root, llm = spans["evaluate-characteristic"], spans["FakeListChatModel"]
    assert root.parent is None
    assert llm.parent is not None and llm.parent.span_id == root.context.span_id
    root_attrs = attrs(root)
    assert root_attrs["langfuse.observation.type"] == "agent"
    assert json.loads(str(root_attrs["langfuse.observation.input"])) == {
        "target": "proj",
        "characteristic": "modularity",
    }
    assert json.loads(str(root_attrs["langfuse.observation.output"])) == {"verdict": "fail"}
    assert root_attrs["langfuse.trace.name"] == "evaluate-characteristic"
    assert root_attrs["langfuse.version"] == "1.0"
    for span in (root, llm):
        a = attrs(span)
        assert a["session.id"] == "stability-1"
        assert a["langfuse.environment"] == "test"
        assert a["langfuse.release"] == "rel-123"
        assert a["langfuse.trace.metadata.version"] == "B"
        assert a["langfuse.trace.metadata.run_id"] == "run123"
        assert a["langfuse.trace.metadata.characteristic"] == "modularity"
        assert set(a["langfuse.trace.tags"]) == {"version:B", "characteristic:modularity"}  # type: ignore[arg-type]


def test_keyed_run_without_session_sets_none(
    exporter: tuple[InMemorySpanExporter, Settings],
) -> None:
    memory, settings = exporter
    with traced_run(
        version="B", run_id="r", characteristic=Characteristic.TESTABILITY, settings=settings
    ):
        pass
    obs.build_langfuse_client(settings).flush()
    assert "session.id" not in attrs(spans_by_name(memory)["evaluate-characteristic"])


def test_exception_marks_root_as_error(exporter: tuple[InMemorySpanExporter, Settings]) -> None:
    memory, settings = exporter
    with (
        pytest.raises(RuntimeError, match="boom"),
        traced_run(
            version="B", run_id="r", characteristic=Characteristic.TESTABILITY, settings=settings
        ),
    ):
        raise RuntimeError("boom")
    obs.build_langfuse_client(settings).flush()
    root = attrs(spans_by_name(memory)["evaluate-characteristic"])
    assert root["langfuse.observation.level"] == "ERROR"
    assert root["langfuse.observation.status_message"] == "RuntimeError: boom"


def test_secrets_are_masked_and_empty_hooks_dropped(
    exporter: tuple[InMemorySpanExporter, Settings],
) -> None:
    from langfuse import get_client

    memory, settings = exporter
    client = get_client(public_key=settings.langfuse_public_key)
    with traced_run(
        version="B",
        run_id="r",
        characteristic=Characteristic.MODULARITY,
        input={"file": "OPENAI_API_KEY=sk-abcdefghijklmnopqrstuvwx\nDEBUG=1"},
        settings=settings,
    ):
        client.start_observation(name="PatchToolCallsMiddleware.before_agent", input={}).end()
        client.start_observation(
            name="SomeMiddleware.after_model", input={}, output={"changed": 1}
        ).end()
    client.flush()

    spans = spans_by_name(memory)
    assert "PatchToolCallsMiddleware.before_agent" not in spans
    assert "SomeMiddleware.after_model" in spans  # did something, so it is kept
    root_input = str(attrs(spans["evaluate-characteristic"])["langfuse.observation.input"])
    assert "sk-abcdefghijklmnopqrstuvwx" not in root_input
    assert "OPENAI_API_KEY=[REDACTED]" in root_input
    assert "DEBUG=1" in root_input


def test_unreachable_langfuse_gives_no_trace_url(caplog: pytest.LogCaptureFixture) -> None:
    class Unreachable:
        def get_trace_url(self) -> str:
            raise ConnectionError("down")

    with caplog.at_level(logging.WARNING):
        assert obs._trace_url(Unreachable()) is None  # type: ignore[arg-type]
    assert "trace URL" in caplog.text
