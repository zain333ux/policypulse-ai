from __future__ import annotations

import asyncio
from statistics import mean
from time import perf_counter
from typing import Any

from policypulse_api.config import Settings
from policypulse_api.orchestration import run_explicit_workflow, run_langgraph_workflow
from policypulse_api.schemas import AnalysisRequest, CommentAssessment, PolicyAnalysis, Recommendation


class FakeLlm:
    async def structured(
        self,
        *,
        system_prompt: str,
        user_payload: dict[str, Any],
        response_model: type[Any],
    ) -> Any:
        del system_prompt
        name = response_model.__name__
        if name == "PolicyAnalysis":
            return PolicyAnalysis(
                title="Attendance Policy",
                summary="Students must maintain attendance.",
                main_rules=["Maintain 85% attendance."],
                affected_groups=["Working students"],
                unclear_clauses=["No appeal process is defined."],
                evidence_ids=["POL-001"],
            )
        if name == "CommentCodingPayload":
            return response_model(
                assessments=[
                    CommentAssessment(
                        comment_id=str(comment["id"]),
                        stance="opposition",
                        urgency="high",
                        tone="Concerned",
                        themes=["appeals"],
                        affected_groups=["Working students"],
                    )
                    for comment in user_payload["comments"]
                ]
            )
        if name == "ConcernsPayload":
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
        if name == "GapsPayload":
            return response_model(
                gaps=[
                    {
                        "id": "GAP-001",
                        "title": "Missing appeals",
                        "description": "The policy does not define appeals.",
                        "covered_in_policy": False,
                        "severity": "high",
                        "suggested_fix": "Add an appeal section.",
                        "evidence_ids": ["POL-001", "COM-001"],
                        "concern_ids": ["CON-001"],
                    }
                ]
            )
        if name == "RecommendationsPayload":
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
        raise AssertionError(f"Unexpected model: {name}")


async def _progress(stage_id: str, status: Any, message: str) -> None:
    del stage_id, status, message


def _request() -> AnalysisRequest:
    return AnalysisRequest(
        policy_text=(
            "Students must maintain 85% attendance. "
            "The policy does not describe exemptions or appeals."
        ),
        comments=[
            "Please add a medical appeal process.",
            "Working students need a fair appeal option.",
        ],
    )


async def _time_one(name: str, runs: int) -> tuple[str, float]:
    request = _request()
    settings = Settings(groq_api_key="benchmark-key", analysis_orchestrator=name)
    fn = run_explicit_workflow if name == "python" else run_langgraph_workflow
    timings: list[float] = []
    for _ in range(runs):
        started = perf_counter()
        await fn(request, settings, _progress, llm=FakeLlm())
        timings.append((perf_counter() - started) * 1000)
    return name, round(mean(timings), 2)


async def main() -> None:
    for name, avg_ms in await asyncio.gather(_time_one("python", 50), _time_one("langgraph", 50)):
        print(f"{name}: {avg_ms} ms avg")


if __name__ == "__main__":
    asyncio.run(main())
