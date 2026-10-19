"""Runtime settings, read from environment variables and an optional `.env` file."""

from functools import lru_cache

from pydantic import Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Field names map to upper-case env vars (e.g. `llm_model` -> `LLM_MODEL`)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # `provider:model`, e.g. `openai:cx/gpt-5.6-terra`. Required only when the agent runs.
    llm_model: str | None = None
    openai_api_key: SecretStr | None = None
    openai_base_url: str | None = None

    langfuse_enabled: bool = True
    langfuse_public_key: str | None = None
    langfuse_secret_key: SecretStr | None = None
    langfuse_base_url: str = "https://cloud.langfuse.com"
    # Keeps dev/test traces out of experiment data. Pattern documented by Langfuse.
    langfuse_tracing_environment: str = Field(
        default="development", pattern=r"^[a-z0-9_-]+$", max_length=40
    )
    # Application release; defaults to the git commit of this code (see observability.py).
    langfuse_release: str | None = None

    @field_validator("langfuse_tracing_environment")
    @classmethod
    def _environment_not_reserved(cls, value: str) -> str:
        if value.startswith("langfuse"):
            raise ValueError("Langfuse reserves environments starting with 'langfuse'")
        return value

    @property
    def langfuse_configured(self) -> bool:
        return bool(self.langfuse_enabled and self.langfuse_public_key and self.langfuse_secret_key)


@lru_cache
def get_settings() -> Settings:
    return Settings()
