import pytest
from pydantic import ValidationError

from policypulse_api.schemas import SurveyBlueprint
from policypulse_api.surveys import _remove_unsupported_privacy_claims, build_response_template


def valid_blueprint() -> SurveyBlueprint:
    questions = [
        {
            "id": f"Q-{index:03d}",
            "question": f"Policy consultation question {index}?",
            "type": "paragraph",
            "options": [],
            "required": index <= 2,
            "purpose": "Collect policy feedback.",
        }
        for index in range(1, 9)
    ]
    return SurveyBlueprint.model_validate(
        {
            "title": "Policy Feedback Survey",
            "description": "Review the proposal and share feedback.",
            "policy_summary": "A short policy summary.",
            "sections": [
                {
                    "title": "Policy impact",
                    "description": "",
                    "questions": questions[:4],
                },
                {
                    "title": "Suggested improvements",
                    "description": "",
                    "questions": questions[4:],
                },
            ],
            "sharing_message": "Please complete this consultation.",
            "estimated_minutes": 6,
        }
    )


def test_response_template_contains_all_questions() -> None:
    blueprint = valid_blueprint()
    template = build_response_template(blueprint)

    assert template.startswith("Timestamp,")
    assert "Policy consultation question 1?" in template
    assert "Policy consultation question 8?" in template


def test_survey_rejects_too_few_questions() -> None:
    payload = valid_blueprint().model_dump()
    payload["sections"] = [payload["sections"][0]]

    with pytest.raises(ValidationError):
        SurveyBlueprint.model_validate(payload)


def test_unsupported_confidentiality_claim_is_removed() -> None:
    sanitized = _remove_unsupported_privacy_claims(
        "Your responses will be kept confidential. Thank you for participating."
    )

    assert "confidential" not in sanitized.lower()
    assert "privacy and data-use notice" in sanitized
