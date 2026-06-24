import time

from fastapi.testclient import TestClient

from policypulse_api.main import app


def test_health_and_demo_analysis_flow() -> None:
    with TestClient(app) as client:
        ready = client.get("/health/ready")
        assert ready.status_code == 200

        created = client.post(
            "/v1/analyses",
            json={
                "policy_text": "A sufficiently detailed sample policy for an API integration test.",
                "comments": ["This policy needs a clear appeal process."],
                "demo": True,
            },
            headers={"x-client-id": "test-client"},
        )
        assert created.status_code == 202
        job_id = created.json()["id"]

        deadline = time.monotonic() + 8
        while time.monotonic() < deadline:
            job = client.get(f"/v1/analyses/{job_id}")
            assert job.status_code == 200
            if job.json()["status"] == "completed":
                break
            time.sleep(0.2)
        assert job.json()["status"] == "completed"
        assert job.json()["result"]["concerns"]


def test_parse_endpoint_accepts_text_inputs() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/v1/parse",
            data={
                "policy_text": "Students must maintain attendance. Appeals are not described.",
                "comments_text": "Add medical exemptions.\nCreate an appeal process.",
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert len(payload["policy_paragraphs"]) >= 1
        assert len(payload["comment_sources"]) == 2
