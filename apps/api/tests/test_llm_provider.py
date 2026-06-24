from __future__ import annotations

import pytest

from policypulse_api.config import Settings
from policypulse_api.llm import resolve_provider


def test_resolve_provider_defaults_to_groq_when_available() -> None:
    provider = resolve_provider(Settings(groq_api_key="groq-key"))
    assert provider.provider == "groq"
    assert provider.api_key == "groq-key"
    assert provider.model == "llama-3.3-70b-versatile"


def test_resolve_provider_supports_xai_grok() -> None:
    provider = resolve_provider(Settings(groq_api_key=None, xai_api_key="xai-key"))
    assert provider.provider == "xai"
    assert provider.api_key == "xai-key"
    assert provider.base_url == "https://api.x.ai/v1"
    assert provider.model == "grok-4.3"


def test_resolve_provider_respects_explicit_selection() -> None:
    provider = resolve_provider(
        Settings(
            groq_api_key="groq-key",
            xai_api_key="xai-key",
            llm_provider="xai",
        )
    )
    assert provider.provider == "xai"
    assert provider.api_key == "xai-key"


def test_resolve_provider_requires_key_for_explicit_provider() -> None:
    with pytest.raises(RuntimeError, match="LLM_PROVIDER=xai requires XAI_API_KEY"):
        resolve_provider(Settings(llm_provider="xai"))
