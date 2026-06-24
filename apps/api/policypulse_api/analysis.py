from __future__ import annotations

from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from .config import Settings
from .demo import build_demo_result
from .orchestration import run_selected_workflow
from .schemas import AnalysisJob, AnalysisRequest, AnalysisStatus, StageProgress, StageStatus
from .store import JobStore

ProgressCallback = Callable[[str, StageStatus, str], Awaitable[None]]

STAGES = [
    ("prepare", "Prepare evidence"),
    ("policy", "Extract policy"),
    ("coding", "Code stakeholder comments"),
    ("sentiment", "Calculate sentiment"),
    ("concerns", "Synthesize concerns"),
    ("gaps", "Detect policy gaps"),
    ("recommendations", "Build recommendations"),
    ("quality", "Validate final evidence"),
]


def new_job(job_id: str) -> AnalysisJob:
    return AnalysisJob(
        id=job_id,
        stages=[StageProgress(id=stage_id, label=label) for stage_id, label in STAGES],
    )


async def run_analysis(
    job_id: str,
    request: AnalysisRequest,
    store: JobStore,
    settings: Settings,
) -> None:
    job = await store.get(job_id)
    if not job:
        return

    async def progress(stage_id: str, status: StageStatus, message: str) -> None:
        current = await store.get(job_id)
        if not current:
            return
        for stage in current.stages:
            if stage.id == stage_id:
                stage.status = status
                stage.message = message
        current.status = AnalysisStatus.RUNNING
        await store.set(current)
        await store.publish(
            job_id,
            {"type": "progress", "stage": stage_id, "status": status, "message": message},
        )

    try:
        if request.demo:
            await progress("prepare", StageStatus.RUNNING, "Loading verified sample evidence")
            result = build_demo_result()
            await progress("prepare", StageStatus.COMPLETED, "Indexed the verified sample")
            for stage_id, label in STAGES[1:]:
                await progress(stage_id, StageStatus.RUNNING, f"{label} in the verified sample")
                await progress(stage_id, StageStatus.COMPLETED, f"{label} completed")
        else:
            result = await run_selected_workflow(request, settings, progress)

        completed = await store.get(job_id)
        if completed:
            completed.status = AnalysisStatus.COMPLETED
            completed.result = result
            completed.updated_at = datetime.now(UTC)
            await store.set(completed)
            await store.publish(job_id, {"type": "complete", "status": "completed"})
    except Exception as exc:
        failed = await store.get(job_id)
        if failed:
            failed.status = AnalysisStatus.FAILED
            failed.error = str(exc)
            for stage in failed.stages:
                if stage.status == StageStatus.RUNNING:
                    stage.status = StageStatus.FAILED
                    stage.message = "This stage could not complete"
            await store.set(failed)
            await store.publish(
                job_id,
                {"type": "error", "status": "failed", "message": str(exc)},
            )
