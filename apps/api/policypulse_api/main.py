from __future__ import annotations

import asyncio
import json
import logging
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from typing import Annotated, cast

from fastapi import (
    Depends,
    FastAPI,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, StreamingResponse

from .analysis import new_job, run_analysis
from .config import get_settings
from .parsers import parse_comments_bytes, parse_comments_text, parse_policy_bytes
from .reports import build_markdown, build_pdf
from .schemas import (
    AnalysisCreated,
    AnalysisJob,
    AnalysisRequest,
    AnalysisStatus,
    GoogleFormDeployment,
    GoogleFormRequest,
    ParseResponse,
    ReportRequest,
    SurveyBlueprint,
    SurveyRequest,
)
from .sources import create_comment_sources, split_policy_paragraphs
from .store import JobStore
from .surveys import build_response_template, create_google_form, generate_survey_blueprint

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("policypulse")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    app.state.store = JobStore(get_settings())
    app.state.analysis_tasks = set()
    yield
    tasks: set[asyncio.Task[None]] = app.state.analysis_tasks
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


app = FastAPI(
    title="PolicyPulse AI API",
    version="1.0.0",
    description="Evidence-first public consultation analysis API.",
    lifespan=lifespan,
)
settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.frontend_origin.split(",")],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


def get_store(request: Request) -> JobStore:
    return cast(JobStore, request.app.state.store)


@app.middleware("http")
async def request_context(request: Request, call_next):  # type: ignore[no-untyped-def]
    request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
    started = datetime.now(UTC)
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_failed", extra={"request_id": request_id, "path": request.url.path})
        raise
    response.headers["x-request-id"] = request_id
    response.headers["x-content-type-options"] = "nosniff"
    response.headers["referrer-policy"] = "strict-origin-when-cross-origin"
    elapsed = (datetime.now(UTC) - started).total_seconds()
    logger.info(
        "request_complete request_id=%s method=%s path=%s status=%s seconds=%.3f",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        elapsed,
    )
    return response


@app.get("/health/live")
async def health_live() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready")
async def health_ready() -> dict[str, str | bool]:
    return {
        "status": "ready",
        "live_ai_configured": bool(settings.groq_api_key),
        "google_forms_configured": bool(settings.google_script_url and settings.google_script_secret),
    }


@app.post("/v1/parse", response_model=ParseResponse)
async def parse_inputs(
    policy_file: Annotated[UploadFile | None, File()] = None,
    comments_file: Annotated[UploadFile | None, File()] = None,
    policy_text: Annotated[str, Form()] = "",
    comments_text: Annotated[str, Form()] = "",
) -> ParseResponse:
    parsed_policy = policy_text.strip()
    parsed_comments = parse_comments_text(comments_text)
    warnings: list[str] = []
    policy_metadata: dict[str, str | int | bool] = {"format": "pasted text"}
    comments_metadata: dict[str, str | int | bool] = {"format": "pasted text"}
    if policy_file:
        content = await policy_file.read()
        _validate_size(content)
        parsed_policy_file = parse_policy_bytes(policy_file.filename or "policy.txt", content)
        parsed_policy = parsed_policy_file.text
        warnings.extend(parsed_policy_file.warnings)
        policy_metadata = parsed_policy_file.metadata
    if comments_file:
        content = await comments_file.read()
        _validate_size(content)
        parsed_comment_file = parse_comments_bytes(comments_file.filename or "comments.txt", content)
        parsed_comments = parsed_comment_file.comments
        warnings.extend(parsed_comment_file.warnings)
        comments_metadata = parsed_comment_file.metadata
    _validate_inputs(parsed_policy, parsed_comments)
    return ParseResponse(
        policy_text=parsed_policy,
        comments=parsed_comments,
        policy_paragraphs=split_policy_paragraphs(parsed_policy),
        comment_sources=create_comment_sources(parsed_comments),
        warnings=warnings,
        policy_metadata=policy_metadata,
        comments_metadata=comments_metadata,
    )


@app.post("/v1/policies/parse", response_model=ParseResponse)
async def parse_policy_input(
    policy_file: Annotated[UploadFile | None, File()] = None,
    policy_text: Annotated[str, Form()] = "",
) -> ParseResponse:
    parsed_policy = policy_text.strip()
    warnings: list[str] = []
    metadata: dict[str, str | int | bool] = {"format": "pasted text"}
    if policy_file:
        content = await policy_file.read()
        _validate_size(content)
        parsed = parse_policy_bytes(policy_file.filename or "policy.txt", content)
        parsed_policy = parsed.text
        warnings = parsed.warnings
        metadata = parsed.metadata
    if len(parsed_policy) < 20:
        raise HTTPException(status_code=422, detail="Provide a policy with at least 20 characters.")
    return ParseResponse(
        policy_text=parsed_policy,
        policy_paragraphs=split_policy_paragraphs(parsed_policy),
        warnings=warnings,
        policy_metadata=metadata,
    )


@app.post("/v1/analyses", response_model=AnalysisCreated, status_code=202)
async def create_analysis(
    payload: AnalysisRequest,
    request: Request,
    store: Annotated[JobStore, Depends(get_store)],
) -> AnalysisCreated:
    _validate_inputs(payload.policy_text, payload.comments)
    client_key = _client_key(request)
    limit = settings.guest_demo_daily_limit if payload.demo else settings.analysis_daily_limit
    count = await store.increment_limit(f"policypulse:limit:{client_key}")
    if count > limit:
        raise HTTPException(
            status_code=429,
            detail="Daily analysis limit reached. The verified sample remains available.",
        )
    job_id = str(uuid.uuid4())
    job = new_job(job_id)
    await store.set(job)
    await store.publish(job_id, {"type": "created", "status": "queued"})
    task = asyncio.create_task(run_analysis(job_id, payload, store, settings))
    tasks: set[asyncio.Task[None]] = request.app.state.analysis_tasks
    tasks.add(task)
    task.add_done_callback(tasks.discard)
    return AnalysisCreated(id=job_id, status=AnalysisStatus.QUEUED)


@app.get("/v1/analyses/{job_id}", response_model=AnalysisJob)
async def get_analysis(
    job_id: str,
    store: Annotated[JobStore, Depends(get_store)],
) -> AnalysisJob:
    job = await store.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Analysis not found or expired.")
    return job


@app.get("/v1/analyses/{job_id}/events")
async def analysis_events(
    job_id: str,
    store: Annotated[JobStore, Depends(get_store)],
) -> StreamingResponse:
    if not await store.get(job_id):
        raise HTTPException(status_code=404, detail="Analysis not found or expired.")

    async def event_stream() -> AsyncIterator[str]:
        index = 0
        while True:
            events, index = await store.events_after(job_id, index)
            for event in events:
                yield f"data: {json.dumps(event)}\n\n"
            job = await store.get(job_id)
            if not job or job.status in {AnalysisStatus.COMPLETED, AnalysisStatus.FAILED}:
                break
            yield ": keep-alive\n\n"
            await asyncio.sleep(0.75)

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.post("/v1/reports/export")
async def export_report(payload: ReportRequest) -> Response:
    if payload.format == "markdown":
        return Response(
            content=build_markdown(payload.result),
            media_type="text/markdown",
            headers={"Content-Disposition": 'attachment; filename="policypulse-report.md"'},
        )
    return Response(
        content=build_pdf(payload.result),
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="policypulse-report.pdf"'},
    )


@app.post("/v1/surveys/generate", response_model=SurveyBlueprint)
async def generate_survey(payload: SurveyRequest) -> SurveyBlueprint:
    try:
        return await generate_survey_blueprint(payload.policy_text, settings)
    except Exception as exc:
        logger.exception("generate_survey failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/v1/surveys/google-form", response_model=GoogleFormDeployment)
async def deploy_survey(payload: GoogleFormRequest) -> GoogleFormDeployment:
    try:
        return await create_google_form(payload.blueprint, settings)
    except Exception as exc:
        logger.exception("deploy_survey failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.post("/v1/surveys/response-template")
async def export_survey_response_template(payload: GoogleFormRequest) -> Response:
    return Response(
        content=build_response_template(payload.blueprint),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="policy-survey-responses.csv"'},
    )


def _validate_size(content: bytes) -> None:
    if len(content) > settings.max_upload_bytes:
        raise HTTPException(status_code=413, detail="File exceeds the 5 MB upload limit.")


def _validate_inputs(policy_text: str, comments: list[str]) -> None:
    if len(policy_text.strip()) < 20:
        raise HTTPException(status_code=422, detail="Provide a policy with at least 20 characters.")
    if len(policy_text) > settings.max_policy_characters:
        raise HTTPException(status_code=422, detail="Policy exceeds the 50,000 character limit.")
    if not comments:
        raise HTTPException(status_code=422, detail="Provide at least one feedback comment.")
    if len(comments) > settings.max_comments:
        raise HTTPException(status_code=422, detail="Feedback exceeds the 500 comment limit.")
    if any(len(comment) > settings.max_comment_characters for comment in comments):
        raise HTTPException(status_code=422, detail="An individual comment exceeds 4,000 characters.")
    if sum(len(comment) for comment in comments) > settings.max_total_comment_characters:
        raise HTTPException(
            status_code=422,
            detail="Combined feedback exceeds the 250,000 character analysis limit.",
        )


def _client_key(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = forwarded.split(",")[0].strip() or (request.client.host if request.client else "unknown")
    browser = request.headers.get("x-client-id", "anonymous")
    return f"{ip}:{browser}"[:180]
