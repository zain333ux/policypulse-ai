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
