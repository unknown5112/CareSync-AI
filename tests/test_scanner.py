"""Tests for Gemini AI scanner, model fallback chain, caching, and downsampling."""

import io
from unittest.mock import MagicMock, patch
from PIL import Image
import pytest
from backend.utils.ai_scanner import (
    FALLBACK_MODELS,
    SCAN_CACHE,
    compute_image_hash,
    optimize_image_for_ai,
    scan_medication_strip,
)


def create_sample_image(size=(1200, 1600), format="JPEG") -> bytes:
    """Helper to generate in-memory image bytes."""
    buf = io.BytesIO()
    img = Image.new("RGB", size, color="green")
    img.save(buf, format=format)
    return buf.getvalue()


def test_image_optimization_and_downsampling():
    """6. Test that oversized images (>1024) are downsampled to max 1024 preserving aspect ratio."""
    large_bytes = create_sample_image(size=(1200, 1600))
    optimized_img, compressed_bytes = optimize_image_for_ai(large_bytes, max_dim=1024)

    assert optimized_img.size[1] == 1024
    assert optimized_img.size[0] == 768  # 1200 * (1024/1600) = 768
    assert len(compressed_bytes) > 0


def test_sha256_bounded_lru_cache():
    """7. Test in-memory SHA-256 LRU cache returns instant hit without external API call."""
    SCAN_CACHE.clear()
    img_bytes = create_sample_image(size=(50, 50))
    img_hash = compute_image_hash(img_bytes)

    # Pre-populate cache
    SCAN_CACHE[img_hash] = {
        "medication_name": "Aspirin Cardio",
        "suggested_dosage": "100mg daily",
        "strength": "100mg",
        "instructions": "Take with water.",
        "confidence": "high",
        "raw_response": "{}",
        "from_cache": False,
    }

    result = scan_medication_strip(img_bytes)
    assert result["from_cache"] is True
    assert result["medication_name"] == "Aspirin Cardio"


@patch("backend.utils.ai_scanner.genai.GenerativeModel")
@patch("backend.utils.ai_scanner.get_settings")
def test_gemini_fallback_model_chain(mock_settings, mock_model_cls):
    """8. Test that 404 on initial model gracefully triggers subsequent model in exact fallback sequence."""
    SCAN_CACHE.clear()
    mock_settings.return_value.gemini_api_key = "test_key"

    first_fail_model = MagicMock()
    first_fail_model.generate_content.side_effect = Exception("404 Not Found: Model gemini-3.1-flash-lite not found")

    second_success_model = MagicMock()
    mock_response = MagicMock()
    mock_response.text = '{"medication_name": "Atorvastatin", "suggested_dosage": "20mg at night", "confidence": "high"}'
    second_success_model.generate_content.return_value = mock_response

    # First call returns failing model, second call returns working model
    mock_model_cls.side_effect = [first_fail_model, second_success_model]

    img_bytes = create_sample_image(size=(100, 100))
    result = scan_medication_strip(img_bytes)

    assert result["medication_name"] == "Atorvastatin"
    assert result["confidence"] == "high"

    # Verify both models in the exact fallback order were tried
    assert mock_model_cls.call_args_list[0][0][0] == FALLBACK_MODELS[0]  # gemini-3.1-flash-lite
    assert mock_model_cls.call_args_list[1][0][0] == FALLBACK_MODELS[1]  # gemini-3.7-flash
