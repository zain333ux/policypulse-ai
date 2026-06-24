from __future__ import annotations

import csv
import re
from io import StringIO

import httpx

from .config import Settings
from .llm import LlmService
from .prompts import POLICY_EXTRACTION_PROMPT, SURVEY_DESIGN_PROMPT
from .schemas import (
    GoogleFormDeployment,
    PolicyAnalysis,
    SurveyBlueprint,
)
from .sources import split_policy_paragraphs


async def generate_survey_blueprint(policy_text: str, settings: Settings) -> SurveyBlueprint:
    sources = split_policy_paragraphs(policy_text)
    llm = LlmService(settings)
    policy = await llm.structured(
        system_prompt=POLICY_EXTRACTION_PROMPT,
        user_payload={"policy_paragraphs": [source.model_dump(mode="json") for source in sources]},
        response_model=PolicyAnalysis,
    )
    blueprint = await llm.structured(
        system_prompt=SURVEY_DESIGN_PROMPT,
        user_payload={
            "policy_analysis": policy.model_dump(mode="json"),
            "policy_passages": [source.model_dump(mode="json") for source in sources],
        },
        response_model=SurveyBlueprint,
    )
    blueprint.description = _remove_unsupported_privacy_claims(blueprint.description)
    blueprint.sharing_message = _remove_unsupported_privacy_claims(blueprint.sharing_message)
    return blueprint


async def create_google_form(
    blueprint: SurveyBlueprint,
    settings: Settings,
) -> GoogleFormDeployment:
    if not settings.google_script_url or not settings.google_script_secret:
        raise RuntimeError(
            "Google Forms creation is not configured. Deploy the included Apps Script connector "
            "and set GOOGLE_SCRIPT_URL and GOOGLE_SCRIPT_SECRET."
        )
    payload = {
        "action": "create_form",
        "secret": settings.google_script_secret,
        "blueprint": blueprint.model_dump(mode="json"),
    }
    async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
        response = await client.post(settings.google_script_url, json=payload)
        response.raise_for_status()
        try:
            data = response.json()
        except ValueError as exc:
            raise RuntimeError(
                "Google Forms connector returned an invalid response. "
                "Confirm the Apps Script deployment runs as the owner and is accessible to anyone."
            ) from exc
    if not data.get("ok"):
        raise RuntimeError(data.get("error", "Google Forms creation failed."))
    return GoogleFormDeployment.model_validate(data["deployment"])


def build_response_template(blueprint: SurveyBlueprint) -> str:
    output = StringIO()
    writer = csv.writer(output)
    headers = ["Timestamp"]
    for section in blueprint.sections:
        headers.extend(question.question for question in section.questions)
    writer.writerow(headers)
    return output.getvalue()


def _remove_unsupported_privacy_claims(value: str) -> str:
    replacement = "Review the form owner's privacy and data-use notice before responding."
    patterns = [
        r"(?i)\ball responses will be (kept )?(anonymous|confidential)\.?",
        r"(?i)\byour responses will be (kept )?(anonymous|confidential)\.?",
        r"(?i)\bresponses are (anonymous|confidential)\.?",
    ]
    sanitized = value
    for pattern in patterns:
        sanitized = re.sub(pattern, replacement, sanitized)
    return re.sub(r"\s{2,}", " ", sanitized).strip()
