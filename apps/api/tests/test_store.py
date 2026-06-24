import pytest

from policypulse_api.config import Settings
from policypulse_api.store import JobStore


@pytest.mark.asyncio
async def test_local_rate_limit_counter_is_independent_per_key() -> None:
    store = JobStore(Settings(upstash_redis_rest_url=None, upstash_redis_rest_token=None))

    assert await store.increment_limit("client-a") == 1
    assert await store.increment_limit("client-a") == 2
    assert await store.increment_limit("client-b") == 1
