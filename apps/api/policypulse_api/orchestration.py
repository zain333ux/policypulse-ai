from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Literal, TypedDict, cast

from pydantic import BaseModel

from .config import Settings
from .llm import LlmService
from .prompts import (
    COMMENT_CODING_PROMPT,
    CONCERN_SYNTHESIS_PROMPT,
    GAP_DETECTION_PROMPT,
    POLICY_EXTRACTION_PROMPT,
    RECOMMENDATION_PROMPT,
)
from .schemas import (
    AnalysisRequest,
    AnalysisResult,
    CommentAssessment,
    Concern,
    Gap,
    PolicyAnalysis,
    Recommendation,
    Sentiment,
    SourceItem,
    StageStatus,
)
from .sources import create_comment_sources, split_policy_paragraphs

ProgressCallback = Callable[[str, StageStatus, str], Awaitable[None]]
OrchestratorName = Literal["python", "langgraph"]


class CommentCodingPayload(BaseModel):
    assessments: list[CommentAssessment]


class ConcernDraft(BaseModel):
    id: str
    theme: str
    summary: str
    urgency: str
    evidence_ids: list[str]
    limited_evidence: bool = False


class ConcernsPayload(BaseModel):
    concerns: list[ConcernDraft]


class GapsPayload(BaseModel):
    gaps: list[Gap]


class RecommendationsPayload(BaseModel):
    recommendations: list[Recommendation]
    executive_memo: str


class WorkflowState(TypedDict, total=False):
    request: AnalysisRequest
    settings: Settings
    progress: ProgressCallback
    llm: LlmService
    orchestrator: OrchestratorName
    policy_sources: list[SourceItem]
    comment_sources: list[SourceItem]
    sources: list[SourceItem]
    source_ids: set[str]
    policy_data: list[dict[str, object]]
    comment_data: list[dict[str, object]]
    policy: PolicyAnalysis
    assessments: list[CommentAssessment]
    sentiment: Sentiment
    concerns: list[Concern]
    gaps: list[Gap]
    recommendations: list[Recommendation]
    executive_memo: str


def get_orchestrator_name(settings: Settings) -> OrchestratorName:
    configured = settings.analysis_orchestrator
    if configured not in {"python", "langgraph"}:
        raise ValueError(f"Unsupported analysis orchestrator: {configured}")
    return cast(OrchestratorName, configured)


async def run_selected_workflow(
    request: AnalysisRequest,
    settings: Settings,
    progress: ProgressCallback,
) -> AnalysisResult:
    orchestrator = get_orchestrator_name(settings)
    if orchestrator == "langgraph":
        return await run_langgraph_workflow(request, settings, progress)
    return await run_explicit_workflow(request, settings, progress)


async def run_explicit_workflow(
    request: AnalysisRequest,
    settings: Settings,
    progress: ProgressCallback,
    llm: LlmService | None = None,
) -> AnalysisResult:
    state = await _prepare_state(request, settings, progress, llm=llm, orchestrator="python")
    policy_state, assessments_state = await asyncio.gather(
        _run_policy_stage(state),
        _run_comment_coding_stage(state),
    )
    state.update(policy_state)
    state.update(assessments_state)
    state.update(await _run_sentiment_stage(state))
    state.update(await _run_concerns_stage(state))
    state.update(await _run_gaps_stage(state))
    state.update(await _run_recommendations_stage(state))
    state.update(await _run_quality_stage(state))
    return _build_result(state)


async def run_langgraph_workflow(
    request: AnalysisRequest,
    settings: Settings,
    progress: ProgressCallback,
    llm: LlmService | None = None,
) -> AnalysisResult:
    try:
        from langgraph.graph import END, START, StateGraph
    except ImportError as exc:  # pragma: no cover - exercised only when optional dep missing
        raise RuntimeError(
            "LangGraph orchestration requires the optional 'langgraph' dependency."
        ) from exc

    state = await _prepare_state(request, settings, progress, llm=llm, orchestrator="langgraph")
    graph = StateGraph(WorkflowState)
    graph.add_node("policy", _run_policy_stage)
    graph.add_node("coding", _run_comment_coding_stage)
    graph.add_node("sentiment", _run_sentiment_stage)
    graph.add_node("concerns", _run_concerns_stage)
    graph.add_node("gaps", _run_gaps_stage)
    graph.add_node("recommendations", _run_recommendations_stage)
    graph.add_node("quality", _run_quality_stage)
    graph.add_edge(START, "policy")
    graph.add_edge(START, "coding")
    graph.add_edge("policy", "sentiment")
    graph.add_edge("coding", "sentiment")
    graph.add_edge("sentiment", "concerns")
    graph.add_edge("concerns", "gaps")
    graph.add_edge("gaps", "recommendations")
    graph.add_edge("recommendations", "quality")
    graph.add_edge("quality", END)
    compiled = graph.compile()
    final_state = cast(WorkflowState, await compiled.ainvoke(state))
    return _build_result(final_state)


async def _prepare_state(
    request: AnalysisRequest,
    settings: Settings,
    progress: ProgressCallback,
    *,
    llm: LlmService | None,
    orchestrator: OrchestratorName,
) -> WorkflowState:
    await progress("prepare", StageStatus.RUNNING, "Indexing policy passages and comments")
    policy_sources = split_policy_paragraphs(request.policy_text)
    comment_sources = create_comment_sources(request.comments)
    sources = [*policy_sources, *comment_sources]
    await progress("prepare", StageStatus.COMPLETED, f"Indexed {len(sources)} evidence items")
    return WorkflowState(
        request=request,
        settings=settings,
        progress=progress,
        llm=llm or LlmService(settings),
        orchestrator=orchestrator,
        policy_sources=policy_sources,
        comment_sources=comment_sources,
        sources=sources,
        source_ids={source.id for source in sources},
        policy_data=[source.model_dump(mode="json") for source in policy_sources],
        comment_data=[source.model_dump(mode="json") for source in comment_sources],
    )


async def _run_policy_stage(state: WorkflowState) -> WorkflowState:
    progress = state["progress"]
    await progress("policy", StageStatus.RUNNING, "Extracting rules and affected groups")
    policy = await state["llm"].structured(
        system_prompt=POLICY_EXTRACTION_PROMPT,
        user_payload={"policy_paragraphs": state["policy_data"]},
        response_model=PolicyAnalysis,
    )
    _validate_evidence(policy.evidence_ids, state["source_ids"])
    await progress("policy", StageStatus.COMPLETED, "Policy structure extracted")
    return {"policy": policy}


async def _run_comment_coding_stage(state: WorkflowState) -> WorkflowState:
    progress = state["progress"]
    await progress("coding", StageStatus.RUNNING, "Coding each comment independently")
    assessments = await _code_comments(state["llm"], state["comment_data"])
    await progress("coding", StageStatus.COMPLETED, f"Coded {len(assessments)} comments")
    return {"assessments": assessments}


async def _run_sentiment_stage(state: WorkflowState) -> WorkflowState:
    progress = state["progress"]
    await progress("sentiment", StageStatus.RUNNING, "Aggregating coded comment stances")
    sentiment = _calculate_sentiment(state["assessments"])
    await progress("sentiment", StageStatus.COMPLETED, "Sentiment calculated from comment-level codes")
    return {"sentiment": sentiment}


async def _run_concerns_stage(state: WorkflowState) -> WorkflowState:
    progress = state["progress"]
    await progress("concerns", StageStatus.RUNNING, "Synthesizing non-overlapping concern themes")
    concerns_payload = await state["llm"].structured(
        system_prompt=CONCERN_SYNTHESIS_PROMPT,
        user_payload={
            "comments": state["comment_data"],
            "comment_assessments": [item.model_dump(mode="json") for item in state["assessments"]],
        },
        response_model=ConcernsPayload,
    )
    concerns = _finalize_concerns(
        concerns_payload.concerns,
        state["source_ids"],
        len(state["comment_sources"]),
    )
    await progress("concerns", StageStatus.COMPLETED, f"Synthesized {len(concerns)} concern themes")
    return {"concerns": concerns}


async def _run_gaps_stage(state: WorkflowState) -> WorkflowState:
    progress = state["progress"]
    await progress("gaps", StageStatus.RUNNING, "Comparing policy coverage with public concerns")
    gaps_payload = await state["llm"].structured(
        system_prompt=GAP_DETECTION_PROMPT,
        user_payload={
            "policy": state["policy"].model_dump(mode="json"),
            "concerns": [concern.model_dump(mode="json") for concern in state["concerns"]],
            "sources": [source.model_dump(mode="json") for source in state["sources"]],
        },
        response_model=GapsPayload,
    )
    concern_ids = {concern.id for concern in state["concerns"]}
    for gap in gaps_payload.gaps:
        _validate_evidence(gap.evidence_ids, state["source_ids"])
        _validate_references(gap.concern_ids, concern_ids, "concern")
    await progress("gaps", StageStatus.COMPLETED, "Coverage gaps validated")
    return {"gaps": gaps_payload.gaps}


async def _run_recommendations_stage(state: WorkflowState) -> WorkflowState:
    progress = state["progress"]
    await progress("recommendations", StageStatus.RUNNING, "Prioritizing practical improvements")
    recommendations_payload = await state["llm"].structured(
        system_prompt=RECOMMENDATION_PROMPT,
        user_payload={
            "policy": state["policy"].model_dump(mode="json"),
            "sentiment": state["sentiment"].model_dump(mode="json"),
            "concerns": [concern.model_dump(mode="json") for concern in state["concerns"]],
            "gaps": {"gaps": [gap.model_dump(mode="json") for gap in state["gaps"]]},
        },
        response_model=RecommendationsPayload,
    )
    gap_ids = {gap.id for gap in state["gaps"]}
    for recommendation in recommendations_payload.recommendations:
        _validate_evidence(recommendation.evidence_ids, state["source_ids"])
        _validate_references(recommendation.gap_ids, gap_ids, "gap")
    await progress("recommendations", StageStatus.COMPLETED, "Recommendations ready for review")
    return {
        "recommendations": recommendations_payload.recommendations,
        "executive_memo": recommendations_payload.executive_memo,
    }


async def _run_quality_stage(state: WorkflowState) -> WorkflowState:
    progress = state["progress"]
    await progress("quality", StageStatus.RUNNING, "Checking references, counts, and readability")
    _validate_unique_ids([item.id for item in state["concerns"]], "concern")
    _validate_unique_ids([item.id for item in state["gaps"]], "gap")
    _validate_unique_ids([item.id for item in state["recommendations"]], "recommendation")
    await progress("quality", StageStatus.COMPLETED, "All final evidence references validated")
    return {}


def _build_result(state: WorkflowState) -> AnalysisResult:
    orchestrator = state["orchestrator"]
    methodology = (
        "PolicyPulse indexed each policy passage and comment, then ran specialized extraction, "
        "comment-level coding, deterministic sentiment aggregation, concern synthesis, "
        "gap detection, and recommendation stages with schema and evidence validation."
    )
    if orchestrator == "langgraph":
        methodology += " Execution was coordinated through a LangGraph state graph."
    else:
        methodology += " Execution was coordinated through the explicit Python workflow."
    return AnalysisResult(
        policy=state["policy"],
        sentiment=state["sentiment"],
        concerns=state["concerns"],
        gaps=state["gaps"],
        recommendations=state["recommendations"],
        executive_memo=state["executive_memo"],
        methodology=methodology,
        limitations=[
            "AI-generated analysis requires human review.",
            "Frequency reflects the uploaded comments and is not representative polling.",
            "This report is not legal advice.",
        ],
        ingestion_warnings=state["request"].ingestion_warnings,
        sources=state["sources"],
    )


def _validate_evidence(ids: list[str], allowed: set[str], prefix: str | None = None) -> None:
    invalid = [value for value in ids if value not in allowed or (prefix and not value.startswith(prefix))]
    if invalid:
        raise ValueError(f"AI returned invalid evidence references: {', '.join(invalid)}")


def _validate_references(ids: list[str], allowed: set[str], kind: str) -> None:
    invalid = [value for value in ids if value not in allowed]
    if invalid:
        raise ValueError(f"AI returned invalid {kind} references: {', '.join(invalid)}")


async def _code_comments(llm: LlmService, comments: list[dict[str, object]]) -> list[CommentAssessment]:
    batches = [comments[index : index + 40] for index in range(0, len(comments), 40)]
    payloads = await asyncio.gather(
        *[
            llm.structured(
                system_prompt=COMMENT_CODING_PROMPT,
                user_payload={"comments": batch},
                response_model=CommentCodingPayload,
            )
            for batch in batches
        ]
    )
    assessments = [assessment for payload in payloads for assessment in payload.assessments]
    expected = {str(comment["id"]) for comment in comments}
    actual = [assessment.comment_id for assessment in assessments]
    if set(actual) != expected or len(actual) != len(expected):
        raise ValueError("Comment coding must return every supplied comment exactly once.")
    return assessments


def _calculate_sentiment(assessments: list[CommentAssessment]) -> Sentiment:
    total = len(assessments)
    counts = {
        stance: sum(assessment.stance == stance for assessment in assessments)
        for stance in ("support", "opposition", "neutral")
    }
    support = round(counts["support"] * 100 / total)
    opposition = round(counts["opposition"] * 100 / total)
    neutral = 100 - support - opposition
    urgent = sum(assessment.urgency == "high" for assessment in assessments)
    mood = "High urgency" if urgent / total >= 0.4 else "Constructive and mixed"
    return Sentiment(
        support=support,
        opposition=opposition,
        neutral=neutral,
        overall_mood=mood,
    )


def _finalize_concerns(
    drafts: list[ConcernDraft],
    source_ids: set[str],
    total_comments: int,
) -> list[Concern]:
    concerns: list[Concern] = []
    for index, draft in enumerate(drafts, start=1):
        evidence = list(dict.fromkeys(draft.evidence_ids))
        _validate_evidence(evidence, source_ids, prefix="COM-")
        count = len(evidence)
        if count == 0:
            continue
        concerns.append(
            Concern(
                id=f"CON-{index:03d}",
                theme=draft.theme,
                summary=draft.summary,
                count=count,
                percentage=round(count * 100 / total_comments, 1),
                urgency=draft.urgency,
                evidence_ids=evidence,
                limited_evidence=count < 2,
            )
        )
    if not concerns:
        raise ValueError("Concern synthesis returned no evidence-grounded themes.")
    return concerns


def _validate_unique_ids(ids: list[str], kind: str) -> None:
    if len(ids) != len(set(ids)):
        raise ValueError(f"The final {kind} identifiers are not unique.")
