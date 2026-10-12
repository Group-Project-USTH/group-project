import pytest

from maintain_eval.config import Settings


def test_defaults_without_env() -> None:
    settings = Settings()
    assert settings.llm_model is None
    assert settings.langfuse_base_url == "https://cloud.langfuse.com"
    assert settings.langfuse_configured is False


def test_reads_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_MODEL", "openai:some-model")
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    settings = Settings()
    assert settings.llm_model == "openai:some-model"
    assert settings.openai_api_key is not None
    assert settings.openai_api_key.get_secret_value() == "sk-test"
    assert "sk-test" not in repr(settings)
    assert settings.langfuse_configured is True


def test_langfuse_disabled_flag_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LANGFUSE_ENABLED", "false")
    monkeypatch.setenv("LANGFUSE_PUBLIC_KEY", "pk-lf-test")
    monkeypatch.setenv("LANGFUSE_SECRET_KEY", "sk-lf-test")
    assert Settings().langfuse_configured is False
