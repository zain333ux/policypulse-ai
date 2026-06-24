from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

import httpx

from .config import Settings
from .schemas import AnalysisJob


class JobStore:
    """TTL job storage with an optional Upstash REST persistence layer."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._jobs: dict[str, tuple[float, AnalysisJob]] = {}
        self._events: dict[str, list[dict[str, Any]]] = defaultdict(list)
        self._limits: dict[str, tuple[float, int]] = {}
        self._lock = asyncio.Lock()

    async def set(self, job: AnalysisJob) -> None:
        job.updated_at = datetime.now(UTC)
        async with self._lock:
            self._jobs[job.id] = (time.time() + self.settings.job_ttl_seconds, job)
        await self._redis_command(
            "set",
            f"policypulse:job:{job.id}",
            job.model_dump_json(),
            "ex",
            str(self.settings.job_ttl_seconds),
        )

    async def get(self, job_id: str) -> AnalysisJob | None:
        async with self._lock:
            cached = self._jobs.get(job_id)
            if cached and cached[0] > time.time():
                return cached[1]
            self._jobs.pop(job_id, None)

        value = await self._redis_command("get", f"policypulse:job:{job_id}")
        if isinstance(value, str):
            job = AnalysisJob.model_validate_json(value)
            async with self._lock:
                self._jobs[job.id] = (time.time() + self.settings.job_ttl_seconds, job)
            return job
        return None

    async def publish(self, job_id: str, event: dict[str, Any]) -> None:
        event["timestamp"] = datetime.now(UTC).isoformat()
        async with self._lock:
            self._events[job_id].append(event)
            self._events[job_id] = self._events[job_id][-50:]

    async def events_after(self, job_id: str, index: int) -> tuple[list[dict[str, Any]], int]:
        async with self._lock:
            events = self._events.get(job_id, [])
            return events[index:], len(events)

    async def increment_limit(self, key: str, ttl_seconds: int = 86_400) -> int:
        remote_value = await self._redis_command("incr", key)
        if isinstance(remote_value, int | str):
            count = int(remote_value)
            if count == 1:
                await self._redis_command("expire", key, str(ttl_seconds))
            return count

        now = time.time()
        async with self._lock:
            cached = self._limits.get(key)
            count = cached[1] + 1 if cached and cached[0] > now else 1
            self._limits[key] = (now + ttl_seconds, count)
            return count

    async def _redis_command(self, *parts: str) -> Any:
        if not self.settings.upstash_redis_rest_url or not self.settings.upstash_redis_rest_token:
            return None
        url = self.settings.upstash_redis_rest_url.rstrip("/")
        headers = {"Authorization": f"Bearer {self.settings.upstash_redis_rest_token}"}
        try:
            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.post(url, headers=headers, json=list(parts))
                response.raise_for_status()
                return response.json().get("result")
        except (httpx.HTTPError, json.JSONDecodeError):
            return None
