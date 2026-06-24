from __future__ import annotations

import pytest

from policypulse_api.config import Settings
from policypulse_api.llm import resolve_provider


def test_resolve_provider_defaults_to_groq_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    monkeypatch.delenv("XAI_MODEL", raising=False)
    provider = resolve_provider(
        Settings(
            groq_api_key="groq-key",
            groq_model="llama-3.3-70b-versatile",
        )
    )
    assert provider.provider == "groq"
    assert provider.api_key == "groq-key"
    assert provider.model == "llama-3.3-70b-versatile"


def test_resolve_provider_supports_xai_grok(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "xai")
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    provider = resolve_provider(Settings(xai_api_key="xai-key"))
    assert provider.provider == "xai"
    assert provider.api_key == "xai-key"
    assert provider.base_url == "https://api.x.ai/v1"
    assert provider.model == "grok-4.3"


def test_resolve_provider_respects_explicit_selection(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    provider = resolve_provider(
        Settings(
            groq_api_key="groq-key",
            xai_api_key="xai-key",
            llm_provider="xai",
        )
    )
    assert provider.provider == "xai"
    assert provider.api_key == "xai-key"


def test_resolve_provider_requires_key_for_explicit_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_PROVIDER", "xai")
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="LLM_PROVIDER=xai requires XAI_API_KEY"):
        resolve_provider(Settings(llm_provider="xai"))
