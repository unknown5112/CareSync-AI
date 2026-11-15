"""Security and hardening tests: file size limits, MIME validation, integrity, headers, and rate limiting."""

import io
from PIL import Image
import pytest
from fastapi.testclient import TestClient
from backend.core.config import get_settings
from backend.main import app

settings = get_settings()


def test_security_headers_present():
    """9. Test security headers injection (nosniff, DENY, permissions-policy)."""
    settings.test_mode = True
    client = TestClient(app)
    response = client.get("/health")

    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "strict-origin-when-cross-origin"
    assert "camera=(self)" in response.headers["Permissions-Policy"]
    assert "Strict-Transport-Security" in response.headers


def test_payload_too_large_413():
    """10. Test upload payload exceeding 5MB triggers 413 Payload Too Large."""
    settings.test_mode = True
    client = TestClient(app)

    # 5MB + 1KB
    large_payload = b"0" * (5 * 1024 * 1024 + 1024)
    response = client.post(
        "/api/scan-medication",
        files={"file": ("huge_strip.jpg", io.BytesIO(large_payload), "image/jpeg")},
    )
    assert response.status_code == 413
    assert "exceeds maximum allowed limit" in response.json()["detail"]


def test_unsupported_media_type_415():
    """11. Test upload with non-image MIME type triggers 415 Unsupported Media Type."""
    settings.test_mode = True
    client = TestClient(app)

    response = client.post(
        "/api/scan-medication",
        files={"file": ("document.pdf", io.BytesIO(b"%PDF-1.4"), "application/pdf")},
    )
    assert response.status_code == 415
    assert "Unsupported file format" in response.json()["detail"]


def test_corrupt_spoofed_image_400():
    """12. Test upload with spoofed image header triggers 400 Bad Request via PIL.Image.verify()."""
    settings.test_mode = True
    client = TestClient(app)

    # Fake JPEG header with invalid content
    spoofed_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF\x00invalidcorruptedbytes"
    response = client.post(
        "/api/scan-medication",
        files={"file": ("corrupt.jpg", io.BytesIO(spoofed_bytes), "image/jpeg")},
    )
    assert response.status_code == 400
    assert "Invalid or corrupt image" in response.json()["detail"]


def test_sliding_window_rate_limiter_429():
    """13. Test sliding-window rate limiter returns 429 after exceeding 30 requests/min."""
    # Temporarily activate rate limiting
    settings.test_mode = False
    rate_limit_client = TestClient(app)

    for i in range(30):
        res = rate_limit_client.post(
            "/api/caregiver-alert",
            json={
                "caregiver_email": "care@example.com",
                "patient_name": "Senior",
                "alert_type": "missed_dose",
                "details": f"Check {i}",
            },
        )
        assert res.status_code == 200

    # 31st request must trigger 429
    blocked_res = rate_limit_client.post(
        "/api/caregiver-alert",
        json={
            "caregiver_email": "care@example.com",
            "patient_name": "Senior",
            "alert_type": "missed_dose",
            "details": "Check 31",
        },
    )
    assert blocked_res.status_code == 429
    assert "Retry-After" in blocked_res.headers
    assert "Rate limit exceeded" in blocked_res.json()["detail"]

    # Restore test mode
    settings.test_mode = True
