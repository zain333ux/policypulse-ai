from __future__ import annotations

import asyncio
import json
from collections.abc import Awaitable, Callable
from typing import Literal, TypedDict, cast

from pydantic import BaseModel

from .config import Settings
from .llm import LlmService
from .prompts import (
    COMMENT_CODING_PROMPT,
    CONCERN_REDUCTION_PROMPT,
    CONCERN_SYNTHESIS_PROMPT,
    GAP_DETECTION_PROMPT,
    POLICY_EXTRACTION_PROMPT,
    POLICY_REDUCTION_PROMPT,
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

MAX_POLICY_STAGE_CHARS = 10_000
MAX_POLICY_SOURCE_TEXT_CHARS = 900
MAX_POLICY_MAP_CHUNK_CHARS = 6_500
MAX_POLICY_REDUCTION_CHARS = 9_000
MAX_COMMENT_CODING_BATCH_CHARS = 7_000
MAX_COMMENT_CODING_BATCH_ITEMS = 20
MAX_CONCERN_STAGE_CHARS = 10_000
MAX_CONCERN_COMMENT_TEXT_CHARS = 280
MAX_CONCERN_MAP_CHUNK_CHARS = 6_500
MAX_CONCERN_MAP_CHUNK_ITEMS = 24
MAX_CONCERN_REDUCTION_CHARS = 9_000
MAX_GAP_STAGE_CHARS = 10_000
MAX_GAP_POLICY_SOURCE_TEXT_CHARS = 600
MAX_GAP_COMMENT_SOURCE_TEXT_CHARS = 220


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
    ingestion_warnings: list[str]
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
        raise RuntimeError("LangGraph orchestration requires the optional 'langgraph' dependency.") from exc

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
        ingestion_warnings=[*request.ingestion_warnings],
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
    policy = await _extract_policy_analysis(state)
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
    concerns_payload = await _synthesize_concerns(state)
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
        user_payload=_build_gap_payload(state),
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
        ingestion_warnings=state["ingestion_warnings"],
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
    batches = _batch_comment_payloads(comments)
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


async def _extract_policy_analysis(state: WorkflowState) -> PolicyAnalysis:
    compact_sources = [
        _compact_source(source, max_text_chars=MAX_POLICY_SOURCE_TEXT_CHARS) for source in state["policy_sources"]
    ]
    payload = {"policy_paragraphs": compact_sources}
    if _json_size(payload) <= MAX_POLICY_STAGE_CHARS:
        return await state["llm"].structured(
            system_prompt=POLICY_EXTRACTION_PROMPT,
            user_payload=payload,
            response_model=PolicyAnalysis,
        )

    chunks = _chunk_records_by_chars(compact_sources, MAX_POLICY_MAP_CHUNK_CHARS)
    partials = await asyncio.gather(
        *[
            state["llm"].structured(
                system_prompt=POLICY_EXTRACTION_PROMPT,
                user_payload={"policy_paragraphs": chunk},
                response_model=PolicyAnalysis,
            )
            for chunk in chunks
        ]
    )
    for partial in partials:
        _validate_evidence(partial.evidence_ids, state["source_ids"])
    _append_warning(
        state,
        "Large policy text was analyzed in multiple passes to stay within live model limits.",
    )
    return await _merge_policy_analyses(state["llm"], partials)


async def _merge_policy_analyses(llm: LlmService, partials: list[PolicyAnalysis]) -> PolicyAnalysis:
    current = [partial.model_dump(mode="json") for partial in partials]
    while len(current) > 1 and _json_size({"partial_analyses": current}) > MAX_POLICY_REDUCTION_CHARS:
        batches = _chunk_records_by_chars(current, MAX_POLICY_REDUCTION_CHARS)
        reduced = await asyncio.gather(
            *[
                llm.structured(
                    system_prompt=POLICY_REDUCTION_PROMPT,
                    user_payload={"partial_analyses": batch},
                    response_model=PolicyAnalysis,
                )
                for batch in batches
            ]
        )
        current = [item.model_dump(mode="json") for item in reduced]
    return await llm.structured(
        system_prompt=POLICY_REDUCTION_PROMPT,
        user_payload={"partial_analyses": current},
        response_model=PolicyAnalysis,
    )


async def _synthesize_concerns(state: WorkflowState) -> ConcernsPayload:
    dossiers = _build_comment_dossiers(state)
    payload = {
        "total_comments": len(state["comment_sources"]),
        "comment_dossiers": dossiers,
        "comment_assessments": [item.model_dump(mode="json") for item in state["assessments"]],
    }
    if _json_size(payload) <= MAX_CONCERN_STAGE_CHARS:
        return await state["llm"].structured(
            system_prompt=CONCERN_SYNTHESIS_PROMPT,
            user_payload=payload,
            response_model=ConcernsPayload,
        )

    batches = _chunk_records_by_chars(
        dossiers,
        MAX_CONCERN_MAP_CHUNK_CHARS,
        max_items=MAX_CONCERN_MAP_CHUNK_ITEMS,
    )
    partial_payloads = await asyncio.gather(
        *[
            state["llm"].structured(
                system_prompt=CONCERN_SYNTHESIS_PROMPT,
                user_payload={
                    "total_comments": len(state["comment_sources"]),
                    "comment_dossiers": batch,
                    "comment_assessments": _assessments_for_comment_batch(state["assessments"], batch),
                },
                response_model=ConcernsPayload,
            )
            for batch in batches
        ]
    )
    _append_warning(
        state,
        "Large comment evidence was analyzed in multiple passes to stay within live model limits.",
    )
    return await _merge_concern_payloads(state["llm"], partial_payloads, len(state["comment_sources"]))


async def _merge_concern_payloads(
    llm: LlmService,
    partial_payloads: list[ConcernsPayload],
    total_comments: int,
) -> ConcernsPayload:
    current = [concern.model_dump(mode="json") for payload in partial_payloads for concern in payload.concerns]
    while len(current) > 1 and _json_size({"partial_concerns": current}) > MAX_CONCERN_REDUCTION_CHARS:
        batches = _chunk_records_by_chars(current, MAX_CONCERN_REDUCTION_CHARS)
        reduced = await asyncio.gather(
            *[
                llm.structured(
                    system_prompt=CONCERN_REDUCTION_PROMPT,
                    user_payload={"total_comments": total_comments, "partial_concerns": batch},
                    response_model=ConcernsPayload,
                )
                for batch in batches
            ]
        )
        current = [concern.model_dump(mode="json") for payload in reduced for concern in payload.concerns]
    return await llm.structured(
        system_prompt=CONCERN_REDUCTION_PROMPT,
        user_payload={"total_comments": total_comments, "partial_concerns": current},
        response_model=ConcernsPayload,
    )


def _build_gap_payload(state: WorkflowState) -> dict[str, object]:
    concern_evidence_ids = {evidence_id for concern in state["concerns"] for evidence_id in concern.evidence_ids}
    policy_sources = [
        _compact_source(source, max_text_chars=MAX_GAP_POLICY_SOURCE_TEXT_CHARS) for source in state["policy_sources"]
    ]
    comment_sources = [
        _compact_source(source, max_text_chars=MAX_GAP_COMMENT_SOURCE_TEXT_CHARS)
        for source in state["comment_sources"]
        if source.id in concern_evidence_ids
    ]
    selected_policy = _limit_records_by_chars(policy_sources, MAX_GAP_STAGE_CHARS // 2)
    remaining_budget = max(1_000, MAX_GAP_STAGE_CHARS - _json_size(selected_policy))
    selected_comments = _limit_records_by_chars(comment_sources, remaining_budget)
    if _payload_was_condensed(policy_sources, selected_policy) or _payload_was_condensed(
        comment_sources, selected_comments
    ):
        _append_warning(
            state,
            "Gap detection used compact evidence excerpts to stay within live model limits.",
        )
    return {
        "policy": state["policy"].model_dump(mode="json"),
        "concerns": [concern.model_dump(mode="json") for concern in state["concerns"]],
        "sources": [*selected_policy, *selected_comments],
    }


def _build_comment_dossiers(state: WorkflowState) -> list[dict[str, object]]:
    assessments_by_id = {assessment.comment_id: assessment for assessment in state["assessments"]}
    dossiers: list[dict[str, object]] = []
    for source in state["comment_sources"]:
        assessment = assessments_by_id.get(source.id)
        if not assessment:
            continue
        dossiers.append(
            {
                "id": source.id,
                "text": _truncate_text(source.text, MAX_CONCERN_COMMENT_TEXT_CHARS),
                "stance": assessment.stance,
                "urgency": assessment.urgency,
                "tone": assessment.tone,
                "themes": assessment.themes,
                "affected_groups": assessment.affected_groups,
            }
        )
    return dossiers


def _assessments_for_comment_batch(
    assessments: list[CommentAssessment],
    batch: list[dict[str, object]],
) -> list[dict[str, object]]:
    batch_ids = {str(item["id"]) for item in batch}
    return [assessment.model_dump(mode="json") for assessment in assessments if assessment.comment_id in batch_ids]


def _batch_comment_payloads(comments: list[dict[str, object]]) -> list[list[dict[str, object]]]:
    batches: list[list[dict[str, object]]] = []
    current: list[dict[str, object]] = []
    current_size = 0
    for comment in comments:
        comment_size = _json_size(comment)
        next_size = current_size + comment_size
        if current and (len(current) >= MAX_COMMENT_CODING_BATCH_ITEMS or next_size > MAX_COMMENT_CODING_BATCH_CHARS):
            batches.append(current)
            current = []
            current_size = 0
        current.append(comment)
        current_size += comment_size
    if current:
        batches.append(current)
    return batches


def _compact_source(source: SourceItem, *, max_text_chars: int) -> dict[str, object]:
    return {
        "id": source.id,
        "type": source.type.value,
        "text": _truncate_text(source.text, max_text_chars),
    }


def _limit_records_by_chars(records: list[dict[str, object]], max_chars: int) -> list[dict[str, object]]:
    if not records:
        return []
    selected: list[dict[str, object]] = []
    current_size = 0
    for record in records:
        record_size = _json_size(record)
        if selected and current_size + record_size > max_chars:
            break
        selected.append(record)
        current_size += record_size
    return selected or [records[0]]


def _chunk_records_by_chars(
    records: list[dict[str, object]],
    max_chars: int,
    *,
    max_items: int | None = None,
) -> list[list[dict[str, object]]]:
    if not records:
        return []
    batches: list[list[dict[str, object]]] = []
    current: list[dict[str, object]] = []
    current_size = 0
    for record in records:
        record_size = _json_size(record)
        should_split = bool(
            current
            and (current_size + record_size > max_chars or (max_items is not None and len(current) >= max_items))
        )
        if should_split:
            batches.append(current)
            current = []
            current_size = 0
        current.append(record)
        current_size += record_size
    if current:
        batches.append(current)
    return batches


def _payload_was_condensed(
    original_records: list[dict[str, object]],
    selected_records: list[dict[str, object]],
) -> bool:
    if len(selected_records) < len(original_records):
        return True
    selected_by_id = {str(record["id"]): record for record in selected_records}
    for record in original_records:
        selected = selected_by_id.get(str(record["id"]))
        if not selected:
            return True
        if selected != record:
            return True
    return False


def _append_warning(state: WorkflowState, message: str) -> None:
    warnings = state.setdefault("ingestion_warnings", [])
    if message not in warnings and len(warnings) < 20:
        warnings.append(message)


def _truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    if max_chars <= 1:
        return text[:max_chars]
    return f"{text[: max_chars - 1].rstrip()}…"


def _json_size(value: object) -> int:
    return len(json.dumps(value, ensure_ascii=False))


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
