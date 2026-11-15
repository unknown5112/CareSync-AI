import io
import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


class TestCareSyncAI(unittest.TestCase):
    def test_health_check(self):
        """Test 1: Verify health check endpoint returns 200 OK and security headers."""
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertIn("CareSync AI API is operational", data["message"])
        self.assertEqual(data["version"], "1.0.0")

        # Verify security headers
        self.assertEqual(response.headers.get("x-content-type-options"), "nosniff")
        self.assertEqual(response.headers.get("x-frame-options"), "DENY")
        self.assertEqual(response.headers.get("x-xss-protection"), "1; mode=block")

    def test_scan_medication_missing_file(self):
        """Test 2: Verify error handling when medication file is omitted (422 Unprocessable Entity)."""
        response = client.post("/api/scan-medication")
        self.assertEqual(response.status_code, 422)

    def test_scan_medication_empty_file(self):
        """Test 3: Verify rejection of empty image files (400 Bad Request)."""
        empty_file = io.BytesIO(b"")
        response = client.post(
            "/api/scan-medication",
            files={"file": ("empty.jpg", empty_file, "image/jpeg")},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("empty", response.json()["detail"].lower())

    def test_scan_medication_payload_too_large(self):
        """Test 4: Verify rejection of oversized files >5MB (413 Payload Too Large)."""
        large_payload = b"0" * (5 * 1024 * 1024 + 1024)  # 5MB + 1KB
        large_file = io.BytesIO(large_payload)
        response = client.post(
            "/api/scan-medication",
            files={"file": ("large_strip.jpg", large_file, "image/jpeg")},
        )
        self.assertEqual(response.status_code, 413)
        self.assertIn("exceeds the maximum allowed size limit", response.json()["detail"])

    @patch("backend.main.scan_medication_strip")
    def test_scan_medication_success_mocked(self, mock_scanner):
        """Test 5: Verify successful OCR extraction with mocked Gemini AI vision response."""
        mock_scanner.return_value = {
            "medication_name": "Lisinopril",
            "suggested_dosage": "10 mg once daily",
            "strength": "10 mg",
            "instructions": "Take daily in the morning with water.",
            "confidence": "high",
            "raw_response": '{"medication_name": "Lisinopril"}',
        }

        dummy_image = io.BytesIO(b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00")
        response = client.post(
            "/api/scan-medication",
            files={"file": ("lisinopril_strip.jpg", dummy_image, "image/jpeg")},
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["filename"], "lisinopril_strip.jpg")
        self.assertEqual(data["data"]["medication_name"], "Lisinopril")
        self.assertEqual(data["data"]["suggested_dosage"], "10 mg once daily")
        self.assertEqual(data["data"]["confidence"], "high")

    @patch("backend.main.scan_medication_strip")
    def test_scan_medication_error_handling(self, mock_scanner):
        """Test 6: Verify 500 Internal Server Error when AI vision processing throws an exception."""
        mock_scanner.side_effect = RuntimeError("All Gemini models failed to process image.")

        dummy_image = io.BytesIO(b"fake image bytes")
        response = client.post(
            "/api/scan-medication",
            files={"file": ("faulty_strip.jpg", dummy_image, "image/jpeg")},
        )

        self.assertEqual(response.status_code, 500)
        self.assertIn("Gemini AI medication scan failed", response.json()["detail"])


if __name__ == "__main__":
    unittest.main()
