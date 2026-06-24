from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any, Literal, TypeVar

from groq import AsyncGroq
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError

from .config import Settings

ModelT = TypeVar("ModelT", bound=BaseModel)
ProviderName = Literal["groq", "xai"]


@dataclass(frozen=True)
class ProviderConfig:
    provider: ProviderName
    model: str
    api_key: str
    base_url: str | None = None


def resolve_provider(settings: Settings) -> ProviderConfig:
    configured = (settings.llm_provider or "").strip().lower()
    if configured:
        if configured == "groq":
            if not settings.groq_api_key:
                raise RuntimeError("LLM_PROVIDER=groq requires GROQ_API_KEY.")
            return ProviderConfig(provider="groq", model=settings.groq_model, api_key=settings.groq_api_key)
        if configured == "xai":
            if not settings.xai_api_key:
                raise RuntimeError("LLM_PROVIDER=xai requires XAI_API_KEY.")
            return ProviderConfig(
                provider="xai",
                model=settings.xai_model,
                api_key=settings.xai_api_key,
                base_url="https://api.x.ai/v1",
            )
        raise RuntimeError(f"Unsupported LLM_PROVIDER: {settings.llm_provider}")
    if settings.groq_api_key:
        return ProviderConfig(provider="groq", model=settings.groq_model, api_key=settings.groq_api_key)
    if settings.xai_api_key:
        return ProviderConfig(
            provider="xai",
            model=settings.xai_model,
            api_key=settings.xai_api_key,
            base_url="https://api.x.ai/v1",
        )
    raise RuntimeError("Live analysis is unavailable because no supported LLM API key is configured.")


class LlmService:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.provider = resolve_provider(settings)
        if self.provider.provider == "groq":
            self.client: AsyncGroq | AsyncOpenAI = AsyncGroq(
                api_key=self.provider.api_key,
                timeout=settings.llm_timeout_seconds,
                max_retries=2,
            )
        else:
            self.client = AsyncOpenAI(
                api_key=self.provider.api_key,
                base_url=self.provider.base_url,
                timeout=settings.llm_timeout_seconds,
                max_retries=2,
            )

    async def structured(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        response_model: type[ModelT],
    ) -> ModelT:
        last_error: Exception | None = None
        schema = json.dumps(response_model.model_json_schema(), ensure_ascii=False)
        for attempt in range(2):
            repair = ""
            if attempt and last_error:
                repair = (
                    "\nThe previous response failed validation. Correct every error and return "
                    f"the required json shape. Validation error: {last_error}"
                )
            response = await self.client.chat.completions.create(
                model=self.provider.model,
                temperature=0.15,
                response_format={"type": "json_object"},
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "Return valid json only. Do not include markdown or explanatory text.\n"
                            f"{system_prompt}\nThe response must exactly match this JSON Schema:\n"
                            f"{schema}{repair}"
                        ),
                    },
                    {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
                ],
            )
            content = response.choices[0].message.content or "{}"
            try:
                return response_model.model_validate_json(content)
            except (ValidationError, json.JSONDecodeError) as exc:
                last_error = exc
                await asyncio.sleep(0.25)
        raise ValueError(
            f"The AI response from provider '{self.provider.provider}' could not be validated: {last_error}"
        )
