from __future__ import annotations

from typing import Any

import pytest

from policypulse_api.config import Settings
from policypulse_api.orchestration import run_explicit_workflow, run_langgraph_workflow
from policypulse_api.schemas import (
    AnalysisRequest,
    CommentAssessment,
    Concern,
    Gap,
    PolicyAnalysis,
    Recommendation,
    Sentiment,
    StageStatus,
)


class FakeLlm:
    async def structured(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        response_model: type[Any],
    ) -> Any:
        del system_prompt
        if response_model.__name__ == "PolicyAnalysis":
            if "partial_analyses" in user_payload:
                partials = user_payload["partial_analyses"]
                evidence_ids: list[str] = []
                for partial in partials:
                    for evidence_id in partial.get("evidence_ids", []):
                        if evidence_id not in evidence_ids:
                            evidence_ids.append(evidence_id)
                return PolicyAnalysis(
                    title="Attendance Policy",
                    summary="Students must maintain attendance.",
                    main_rules=["Maintain 85% attendance."],
                    affected_groups=["Working students"],
                    unclear_clauses=["No appeal process is defined."],
                    evidence_ids=evidence_ids or ["POL-001"],
                )
            return PolicyAnalysis(
                title="Attendance Policy",
                summary="Students must maintain attendance.",
                main_rules=["Maintain 85% attendance."],
                affected_groups=["Working students"],
                unclear_clauses=["No appeal process is defined."],
                evidence_ids=["POL-001"],
            )
        if response_model.__name__ == "CommentCodingPayload":
            comments = user_payload["comments"]
            return response_model(
                assessments=[
                    CommentAssessment(
                        comment_id=str(comment["id"]),
                        stance="opposition" if "appeal" in str(comment["text"]).lower() else "support",
                        urgency="high",
                        tone="Concerned",
                        themes=["appeals"],
                        affected_groups=["Working students"],
                    )
                    for comment in comments
                ]
            )
        if response_model.__name__ == "ConcernsPayload":
            if "partial_concerns" in user_payload:
                evidence_ids: list[str] = []
                for concern in user_payload["partial_concerns"]:
                    for evidence_id in concern.get("evidence_ids", []):
                        if evidence_id not in evidence_ids:
                            evidence_ids.append(evidence_id)
                if len(evidence_ids) < 2:
                    evidence_ids = ["COM-001", "COM-002"]
                return response_model(
                    concerns=[
                        {
                            "id": "draft-1",
                            "theme": "Appeals",
                            "summary": "Students want an appeal path.",
                            "urgency": "high",
                            "evidence_ids": evidence_ids,
                        }
                    ]
                )
            return response_model(
                concerns=[
                    {
                        "id": "draft-1",
                        "theme": "Appeals",
                        "summary": "Students want an appeal path.",
                        "urgency": "high",
                        "evidence_ids": ["COM-001", "COM-002"],
                    }
                ]
            )
        if response_model.__name__ == "GapsPayload":
            return response_model(
                gaps=[
                    Gap(
                        id="GAP-001",
                        title="Missing appeals",
                        description="The policy does not define appeals.",
                        covered_in_policy=False,
                        severity="high",
                        suggested_fix="Add an appeal section.",
                        evidence_ids=["POL-001", "COM-001"],
                        concern_ids=["CON-001"],
                    )
                ]
            )
        if response_model.__name__ == "RecommendationsPayload":
            return response_model(
                recommendations=[
                    Recommendation(
                        id="REC-001",
                        title="Create appeal process",
                        action="Add a formal appeal path with deadlines.",
                        rationale="This addresses the main concern cluster.",
                        priority="critical",
                        gap_ids=["GAP-001"],
                        evidence_ids=["POL-001", "COM-001"],
                        revised_wording="Students may file an appeal within five working days.",
                    )
                ],
                executive_memo="Leadership should add an appeal process.",
            )
        raise AssertionError(f"Unexpected response model: {response_model.__name__}")


class RecordingFakeLlm(FakeLlm):
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def structured(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        response_model: type[Any],
    ) -> Any:
        del system_prompt
        self.calls.append((response_model.__name__, user_payload))
        return await super().structured(
            system_prompt="",
            user_payload=user_payload,
            response_model=response_model,
        )


async def _progress(stage_id: str, status: StageStatus, message: str) -> None:
    del stage_id, status, message


def _request() -> AnalysisRequest:
    return AnalysisRequest(
        policy_text=("Students must maintain 85% attendance. The policy does not describe exemptions or appeals."),
        comments=[
            "Please add a medical appeal process.",
            "Working students need a fair appeal option.",
        ],
    )


@pytest.mark.asyncio
async def test_explicit_and_langgraph_workflows_match() -> None:
    settings = Settings(groq_api_key="test-key")
    request = _request()

    explicit = await run_explicit_workflow(request, settings, _progress, llm=FakeLlm())
    langgraph = await run_langgraph_workflow(request, settings, _progress, llm=FakeLlm())

    assert explicit.policy == langgraph.policy
    assert (
        explicit.sentiment
        == langgraph.sentiment
        == Sentiment(
            support=0,
            opposition=100,
            neutral=0,
            overall_mood="High urgency",
        )
    )
    assert (
        explicit.concerns
        == langgraph.concerns
        == [
            Concern(
                id="CON-001",
                theme="Appeals",
                summary="Students want an appeal path.",
                count=2,
                percentage=100.0,
                urgency="high",
                evidence_ids=["COM-001", "COM-002"],
                limited_evidence=False,
            )
        ]
    )
    assert explicit.gaps == langgraph.gaps
    assert explicit.recommendations == langgraph.recommendations
    assert "explicit Python workflow" in explicit.methodology
    assert "LangGraph state graph" in langgraph.methodology


@pytest.mark.asyncio
async def test_large_comment_sets_are_condensed_for_live_model_limits() -> None:
    settings = Settings(groq_api_key="test-key")
    request = AnalysisRequest(
        policy_text=(
            "Students must maintain 85% attendance. The policy does not describe exemptions, "
            "medical accommodations, transport hardship support, or a formal appeal route."
        ),
        comments=[
            (
                f"Comment {index} asks for a medical and transport appeal option for working students. "
                + ("This explanation is intentionally long to simulate a large real-world submission. " * 12)
            )
            for index in range(1, 91)
        ],
    )
    llm = RecordingFakeLlm()

    result = await run_explicit_workflow(request, settings, _progress, llm=llm)

    coding_calls = [payload for model_name, payload in llm.calls if model_name == "CommentCodingPayload"]
    concern_calls = [payload for model_name, payload in llm.calls if model_name == "ConcernsPayload"]
    gap_calls = [payload for model_name, payload in llm.calls if model_name == "GapsPayload"]

    assert len(coding_calls) > 1
    assert all(len(payload["comments"]) <= 20 for payload in coding_calls)
    assert len(concern_calls) > 1
    assert any("comment_dossiers" in payload for payload in concern_calls)
    assert any("partial_concerns" in payload for payload in concern_calls)
    assert gap_calls
    assert any("multiple passes" in warning.lower() for warning in result.ingestion_warnings)


@pytest.mark.asyncio
async def test_large_policy_is_reduced_across_multiple_passes() -> None:
    settings = Settings(groq_api_key="test-key")
    request = AnalysisRequest(
        policy_text="\n\n".join(
            f"Clause {index}: Students must follow attendance, conduct, and appeal expectations. "
            + ("Additional implementation detail. " * 25)
            for index in range(1, 30)
        ),
        comments=[
            "Please add an appeal process.",
            "Medical exemptions need to be clearer.",
        ],
    )
    llm = RecordingFakeLlm()

    result = await run_explicit_workflow(request, settings, _progress, llm=llm)

    policy_calls = [payload for model_name, payload in llm.calls if model_name == "PolicyAnalysis"]

    assert len(policy_calls) > 1
    assert any("policy_paragraphs" in payload for payload in policy_calls)
    assert any("partial_analyses" in payload for payload in policy_calls)
    assert any("multiple passes" in warning.lower() for warning in result.ingestion_warnings)
