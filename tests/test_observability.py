import logging

import pytest

from maintain_eval.config import Settings
from maintain_eval.observability import new_run_id, traced_run
from maintain_eval.schemas import Characteristic


def test_no_keys_degrades_to_noop_with_warning(caplog: pytest.LogCaptureFixture) -> None:
    with (
        caplog.at_level(logging.WARNING),
        traced_run(version="B", run_id="r1", characteristic=Characteristic.MODULARITY) as config,
    ):
        assert config["callbacks"] == []
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
        ) as config,
    ):
        assert config["callbacks"] == []
    assert caplog.text == ""


def test_config_carries_run_metadata_and_tags() -> None:
    with traced_run(
        version="B", run_id="abc", characteristic=Characteristic.ANALYSABILITY, tags=["smoke"]
    ) as config:
        assert config["metadata"] == {
            "version": "B",
            "run_id": "abc",
            "characteristic": "analysability",
        }
        assert config["tags"] == ["version:B", "characteristic:analysability", "smoke"]
        assert config["run_name"] == "maintain-eval"


def test_new_run_id_is_unique_and_short() -> None:
    ids = {new_run_id() for _ in range(100)}
    assert len(ids) == 100
    assert all(len(i) == 12 for i in ids)


def test_keyed_path_exports_trace_attributes(monkeypatch: pytest.MonkeyPatch) -> None:
    """With keys set, spans carry the run metadata. Uses an in-memory exporter, no network."""
    from langchain_core.language_models.fake_chat_models import FakeListChatModel
    from langfuse import Langfuse
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    import maintain_eval.observability as obs

    exporter = InMemorySpanExporter()
    client = Langfuse(
        public_key="pk-lf-test",
        secret_key="sk-lf-test",
        base_url="http://127.0.0.1:9",
        span_exporter=exporter,
    )
    monkeypatch.setattr(obs, "_client_initialised", True)
    settings = Settings(langfuse_public_key="pk-lf-test", langfuse_secret_key="sk-lf-test")

    with traced_run(
        version="B", run_id="run123", characteristic=Characteristic.MODULARITY, settings=settings
    ) as config:
        assert len(config["callbacks"]) == 1
        FakeListChatModel(responses=["ok"]).invoke("hi", config=config)
    client.flush()

    (span,) = exporter.get_finished_spans()
    attrs = dict(span.attributes or {})
    assert attrs["session.id"] == "run123"
    assert attrs["langfuse.trace.name"] == "maintain-eval"
    assert attrs["langfuse.trace.metadata.version"] == "B"
    assert attrs["langfuse.trace.metadata.run_id"] == "run123"
    assert attrs["langfuse.trace.metadata.characteristic"] == "modularity"
    assert set(attrs["langfuse.trace.tags"]) == {"version:B", "characteristic:modularity"}
