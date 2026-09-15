"""Typed settings for lango (LG-003).

Code asks `get_settings()` and never reads `os.environ` directly. The API key is a `SecretStr`,
so it prints as '**********', and the Anthropic URL is a constant, so no env var can reroute
traffic.
"""

from functools import lru_cache
from typing import Final, Literal

from pydantic import Field, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ANTHROPIC_BASE_URL: Final[str] = "https://api.anthropic.com"
ANTHROPIC_KEY_PREFIX: Final[str] = "sk-ant-"


class SettingsError(RuntimeError):
    """Settings are invalid. The message names fields and problems, never input values."""


class Settings(BaseSettings):
    """lango's runtime configuration, loaded from environment variables and `.env`."""

    model_config = SettingsConfigDict(
        env_prefix="LANGO_", env_file=".env", extra="ignore", hide_input_in_errors=True
    )

    anthropic_api_key: SecretStr = Field(validation_alias="ANTHROPIC_API_KEY")
    model: Literal["claude-sonnet-5", "claude-haiku-4-5-20251001"] = "claude-sonnet-5"
    my_language: Literal["en"] = "en"
    their_language: Literal["vi"] = "vi"

    @field_validator("anthropic_api_key")
    @classmethod
    def check_key_format(cls, value: SecretStr) -> SecretStr:
        key = value.get_secret_value()
        if not key.startswith(ANTHROPIC_KEY_PREFIX) or len(key) == len(ANTHROPIC_KEY_PREFIX):
            msg = f"Anthropic API key must start with '{ANTHROPIC_KEY_PREFIX}' followed by the key"
            raise ValueError(msg)
        return value


@lru_cache
def get_settings() -> Settings:
    """Build Settings once and reuse it. Tests call `get_settings.cache_clear()` to reset."""
    return Settings()


def load_settings() -> Settings:
    """Load settings at startup, turning validation errors into a key-free `SettingsError`.

    `exc.errors()` includes the raw input (the API key) by default, so it is built with
    `include_input=False`. The raise happens *outside* the `except` block, so the original
    `ValidationError` isn't kept as `__context__` either (LG-003, LG-016 security review).
    """
    try:
        return get_settings()
    except ValidationError as exc:
        problems = [
            f"{'.'.join(str(part) for part in error['loc'])}: {error['msg']}"
            for error in exc.errors(include_input=False, include_url=False)
        ]
    msg = "Invalid lango settings: " + "; ".join(problems)
    raise SettingsError(msg)
