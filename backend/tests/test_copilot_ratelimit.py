"""
Unit tests for AI Copilot endpoint abuse protection:
- Per-IP rate limiting (5 requests/minute)
- Hard daily quota check (Redis + memory fallback)
- Preserved honest fallback when GOOGLE_API_KEY is not configured
- Input validation
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from backend.api.main import app
from backend.utils.limiter import (
    limiter,
    reset_daily_copilot_quota,
    check_and_increment_daily_copilot_quota,
    get_daily_copilot_quota_status,
)


@pytest.fixture(autouse=True)
def reset_limiter_state():
    """Reset SlowAPI and daily quota state before each test."""
    reset_daily_copilot_quota()
    # Reset slowapi in-memory storage if accessible
    try:
        limiter._storage.storage.clear()
    except Exception:
        pass
    yield
    reset_daily_copilot_quota()
    try:
        limiter._storage.storage.clear()
    except Exception:
        pass


def test_copilot_fallback_when_api_key_absent():
    """When GOOGLE_API_KEY is not set, endpoint returns honest guidance with 200 OK."""
    client = TestClient(app, raise_server_exceptions=False)
    with patch("backend.api.copilot.settings.google_api_key", ""):
        response = client.post(
            "/api/v1/copilot/ask",
            json={"question": "What algorithms does Decisera support?"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "answer" in data
        assert (
            "GOOGLE_API_KEY" in data["answer"]
            or "requires a Google API key" in data["answer"]
        )
        assert data["confidence"] == 0.0


def test_copilot_empty_question_rejected():
    """Whitespace or empty question is rejected with 400 Bad Request."""
    client = TestClient(app, raise_server_exceptions=False)
    response = client.post(
        "/api/v1/copilot/ask",
        json={"question": "   "},
    )
    assert response.status_code == 400
    body = response.json()
    error_msg = ""
    if isinstance(body.get("error"), dict):
        error_msg = body["error"].get("message", "")
    elif isinstance(body.get("error"), str):
        error_msg = body["error"]
    else:
        error_msg = body.get("detail", "")
    assert "Question cannot be empty" in error_msg


def test_copilot_rate_limit_exceeded_on_sixth_call():
    """Endpoint allows up to 5 requests per minute, and returns 429 on the 6th call."""
    client = TestClient(app, raise_server_exceptions=False)

    with patch("backend.api.copilot.settings.google_api_key", ""):
        # First 5 calls must succeed (200 OK)
        for i in range(5):
            res = client.post(
                "/api/v1/copilot/ask",
                json={"question": f"Test question number {i + 1}"},
            )
            assert (
                res.status_code == 200
            ), f"Call {i+1} failed with status {res.status_code}"

        # 6th call from same IP must be rate-limited (429 Too Many Requests)
        res_sixth = client.post(
            "/api/v1/copilot/ask",
            json={"question": "Test question number 6 - should be blocked"},
        )
        assert res_sixth.status_code == 429
        body = res_sixth.json()
        error_text = ""
        if isinstance(body.get("error"), dict):
            error_text = body["error"].get("message", "")
        elif isinstance(body.get("error"), str):
            error_text = body["error"]
        else:
            error_text = body.get("detail", "")
        assert "Rate limit exceeded" in error_text


def test_copilot_daily_cap_exceeded():
    """When the daily quota limit is reached, returns 429 with clear daily quota message."""
    client = TestClient(app, raise_server_exceptions=False)

    # Mock daily limit to 2 for deterministic test
    with patch("backend.api.copilot.settings.copilot_daily_limit", 2):
        with patch("backend.api.copilot.settings.google_api_key", ""):
            # 1st call: OK
            res1 = client.post("/api/v1/copilot/ask", json={"question": "Query 1"})
            assert res1.status_code == 200

            # 2nd call: OK
            res2 = client.post("/api/v1/copilot/ask", json={"question": "Query 2"})
            assert res2.status_code == 200

            # 3rd call: Daily limit exceeded
            res3 = client.post("/api/v1/copilot/ask", json={"question": "Query 3"})
            assert res3.status_code == 429
            body = res3.json()
            error_text = ""
            if isinstance(body.get("error"), dict):
                error_text = body["error"].get("message", "")
            elif isinstance(body.get("error"), str):
                error_text = body["error"]
            else:
                error_text = body.get("detail", "")
            assert "Daily AI Copilot request quota exceeded" in error_text
            assert "3/2" in error_text or "quota" in error_text.lower()


def test_copilot_quota_status_tracking():
    """Daily quota status tracking accurately reflects increments."""
    reset_daily_copilot_quota("test-user-ip")

    status_before = get_daily_copilot_quota_status("test-user-ip", limit=10)
    assert status_before["used"] == 0
    assert status_before["remaining"] == 10

    allowed, count, limit = check_and_increment_daily_copilot_quota(
        "test-user-ip", limit=10
    )
    assert allowed is True
    assert count == 1

    status_after = get_daily_copilot_quota_status("test-user-ip", limit=10)
    assert status_after["used"] == 1
    assert status_after["remaining"] == 9
