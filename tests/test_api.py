"""Unit and integration tests for CareSync AI API endpoints."""

import io
from unittest.mock import patch
from PIL import Image
import pytest
from fastapi.testclient import TestClient
from backend.core.config import get_settings
from backend.main import app

# Ensure test mode is active to bypass rate limiting for functional tests
settings = get_settings()
settings.test_mode = True

client = TestClient(app)


def create_test_image_bytes(format="JPEG", size=(100, 100)) -> bytes:
    """Helper creating valid in-memory image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color="blue")
    img.save(buf, format=format)
    return buf.getvalue()


def test_health_endpoint():
    """1. Test GET /health and / returns 200 OK with dependency map."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "CareSync AI API is fully operational" in data["message"]
    assert "dependencies" in data
    assert "gemini_api" in data["dependencies"]


def test_root_health_alias():
    """2. Test root GET / alias matches health check schema."""
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@patch("backend.main.scan_medication_strip")
def test_scan_medication_success(mock_scan):
    """3. Test successful medication scan with mocked Gemini Vision result."""
    mock_scan.return_value = {
        "medication_name": "Metformin HCl",
        "suggested_dosage": "500mg twice daily with meals",
        "strength": "500mg",
        "instructions": "Take with full glass of water.",
        "confidence": "high",
        "raw_response": '{"medication_name": "Metformin HCl"}',
        "from_cache": False,
    }

    img_bytes = create_test_image_bytes()
    response = client.post(
        "/api/scan-medication",
        files={"file": ("metformin.jpg", io.BytesIO(img_bytes), "image/jpeg")},
    )

    assert response.status_code == 200
    res_data = response.json()
    assert res_data["status"] == "success"
    assert res_data["filename"] == "metformin.jpg"
    assert res_data["data"]["medication_name"] == "Metformin HCl"
    assert res_data["data"]["confidence"] == "high"


@patch("backend.main.analyze_drug_interactions")
def test_check_interactions_endpoint(mock_analyze):
    """4. Test POST /api/check-interactions for elderly polypharmacy."""
    mock_analyze.return_value = {
        "severity": "caution",
        "summary": "Metformin combined with Lisinopril may slightly elevate hypotension risk.",
        "recommendation": "Monitor blood pressure regularly and stay hydrated.",
        "raw_response": "{}",
    }

    payload = {
        "new_medication": "Lisinopril",
        "current_medications": ["Metformin 500mg"],
    }
    response = client.post("/api/check-interactions", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["severity"] == "caution"
    assert "Lisinopril" in data["summary"]


@patch("backend.main.send_caregiver_alert_email")
def test_caregiver_alert_endpoint(mock_email):
    """5. Test POST /api/caregiver-alert email dispatch."""
    mock_email.return_value = {"status": "success", "message": "Email sent"}

    payload = {
        "caregiver_email": "caregiver@example.com",
        "patient_name": "Eleanor Vance",
        "alert_type": "sos",
        "details": "Patient triggered emergency assistance on smart dashboard.",
    }
    response = client.post("/api/caregiver-alert", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["alert_type"] == "sos"
