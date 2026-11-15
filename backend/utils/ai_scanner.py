"""Gemini AI multimodal scanner and drug interaction reasoning module for CareSync AI."""

from collections import OrderedDict
import hashlib
import io
import json
import re
import traceback
from typing import Any, Dict, List, Optional, Tuple, Union
import google.generativeai as genai
from PIL import Image
from backend.core.config import get_settings
from backend.core.logging import logger

# Bounded LRU cache for medication strip scans (max 100 entries)
SCAN_CACHE: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
MAX_CACHE_SIZE = 100

# Strict Gemini fallback model sequence
FALLBACK_MODELS: List[str] = [
    "gemini-3.1-flash-lite",
    "gemini-3.7-flash",
    "gemini-omni-flash-preview",
    "gemini-3.8-flash",
]

_gemini_client_configured = False


def get_gemini_client() -> None:
    """Configures the Google Gemini API client singleton."""
    global _gemini_client_configured
    settings = get_settings()
    if not settings.gemini_api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is missing. "
            "Please configure GEMINI_API_KEY in your environment or .env file."
        )
    if not _gemini_client_configured:
        genai.configure(api_key=settings.gemini_api_key)
        _gemini_client_configured = True


def compute_image_hash(image_bytes: bytes) -> str:
    """Computes a SHA-256 hex digest of raw image bytes for bounded LRU caching.

    Args:
        image_bytes: Raw binary content of the image.

    Returns:
        Hexadecimal SHA-256 string.
    """
    return hashlib.sha256(image_bytes).hexdigest()


def optimize_image_for_ai(image_bytes: bytes, max_dim: int = 1024) -> Tuple[Image.Image, bytes]:
    """Validates image integrity and optimizes dimensions/compression for low latency.

    Args:
        image_bytes: Raw binary image payload.
        max_dim: Maximum width or height constraint.

    Returns:
        Tuple of (PIL.Image instance, compressed JPEG bytes).

    Raises:
        ValueError: If the file is corrupt or not a valid readable image.
    """
    try:
        # Integrity verification
        verify_img = Image.open(io.BytesIO(image_bytes))
        verify_img.verify()
    except Exception as verify_err:
        raise ValueError(f"Corrupt or invalid image payload: {verify_err}") from verify_err

    # Reopen for processing after verify()
    img = Image.open(io.BytesIO(image_bytes))

    # Convert RGBA/Palette/CMYK to RGB
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")

    # Resize oversized images preserving aspect ratio
    width, height = img.size
    if width > max_dim or height > max_dim:
        scale = max_dim / max(width, height)
        new_size = (int(width * scale), int(height * scale))
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        logger.info(f"[ImageOptimizer] Resized image from {(width, height)} to {new_size}")

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=85, optimize=True)
    optimized_bytes = buffer.getvalue()
    return img, optimized_bytes


def execute_gemini_fallback_prompt(prompt: str, image: Optional[Image.Image] = None) -> Tuple[str, str]:
    """Executes a prompt across the strict fallback model sequence.

    Args:
        prompt: Clinical instruction prompt.
        image: Optional PIL Image object for vision reasoning.

    Returns:
        Tuple of (raw response text, successful model name).

    Raises:
        RuntimeError: If all models in the sequence fail.
    """
    get_gemini_client()
    last_exception = None

    content_payload = [prompt, image] if image is not None else [prompt]

    for model_name in FALLBACK_MODELS:
        try:
            logger.info(f"[Gemini] Attempting generation with model: {model_name}")
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(content_payload)
            if response and hasattr(response, "text") and response.text:
                logger.info(f"[Gemini] Success with model: {model_name}")
                return response.text.strip(), model_name
        except Exception as err:
            last_exception = err
            err_str = str(err).lower()
            logger.warning(f"[Gemini] Model {model_name} failed: {err}")
            # Continue down the fallback chain
            continue

    if last_exception:
        logger.error(f"[Gemini] All fallback models exhausted. Last error: {last_exception}")
        raise RuntimeError(
            f"All Gemini models in fallback sequence failed. Last error: {str(last_exception)}"
        ) from last_exception
    raise RuntimeError("Gemini API returned an empty or invalid response from all models.")


def scan_medication_strip(
    image_data: Union[bytes, str], mime_type: str = "image/jpeg"
) -> Dict[str, Any]:
    """Extracts medication name, dosage, and instructions from a medication packaging photo.

    Employs SHA-256 caching and the strict Gemini fallback model sequence.

    Args:
        image_data: Raw image bytes or path to file.
        mime_type: MIME type of the image.

    Returns:
        Dictionary containing extracted medication fields.
    """
    if isinstance(image_data, str):
        with open(image_data, "rb") as f:
            image_bytes = f.read()
    elif isinstance(image_data, bytes):
        image_bytes = image_data
    else:
        raise TypeError("image_data must be bytes or a valid file path string.")

    if not image_bytes:
        raise ValueError("Provided image data is empty.")

    # Check bounded SHA-256 LRU cache
    img_hash = compute_image_hash(image_bytes)
    if img_hash in SCAN_CACHE:
        logger.info(f"[ScanCache] Cache hit for hash {img_hash[:12]}...")
        cached_result = dict(SCAN_CACHE[img_hash])
        cached_result["from_cache"] = True
        # Move to end (most recently used)
        SCAN_CACHE.move_to_end(img_hash)
        return cached_result

    # Validate integrity & optimize image
    img, _ = optimize_image_for_ai(image_bytes)

    prompt = (
        "You are an expert geriatric medical AI assistant specialized in analyzing medication packaging and strips. "
        "Analyze this medication image carefully.\n\n"
        "Extract the information and strictly return ONLY a valid JSON object with these exact keys:\n"
        "{\n"
        '  "medication_name": "Exact brand and generic chemical name of the medicine",\n'
        '  "suggested_dosage": "Dosage instructions or strength stated on the packaging",\n'
        '  "strength": "Concentration per tablet/capsule (e.g., 500mg, 10mg) if visible",\n'
        '  "instructions": "Any visible instructions, precautions, or warnings",\n'
        '  "confidence": "high, medium, or low"\n'
        "}\n\n"
        "Do not include markdown fences or any explanation outside the JSON."
    )

    text_output, successful_model = execute_gemini_fallback_prompt(prompt, image=img)

    # Clean potential markdown fences
    cleaned_json_str = re.sub(r"^```(?:json)?\s*", "", text_output, flags=re.MULTILINE)
    cleaned_json_str = re.sub(r"```$", "", cleaned_json_str, flags=re.MULTILINE).strip()

    try:
        parsed_data = json.loads(cleaned_json_str)
    except Exception as parse_err:
        raise RuntimeError(
            f"Failed to parse JSON response from {successful_model}: {parse_err}. Raw text: {text_output}"
        ) from parse_err

    result = {
        "medication_name": parsed_data.get("medication_name", "Unknown Medication"),
        "suggested_dosage": parsed_data.get("suggested_dosage", "Consult doctor/pharmacist"),
        "strength": parsed_data.get("strength"),
        "instructions": parsed_data.get("instructions"),
        "confidence": parsed_data.get("confidence", "high"),
        "raw_response": text_output,
        "from_cache": False,
    }

    # Store in bounded cache
    if len(SCAN_CACHE) >= MAX_CACHE_SIZE:
        SCAN_CACHE.popitem(last=False)  # Evict oldest entry
    SCAN_CACHE[img_hash] = result
    logger.info(f"[ScanCache] Stored scan result in cache for hash {img_hash[:12]}...")

    return result


def analyze_drug_interactions(new_medication: str, current_medications: List[str]) -> Dict[str, Any]:
    """Analyzes drug-drug interactions for an elderly patient against existing prescriptions.

    Uses the exact same Gemini model fallback sequence.

    Args:
        new_medication: Candidate new medication.
        current_medications: List of current medications.

    Returns:
        Dictionary containing severity ('safe' | 'caution' | 'danger'), summary, and recommendation.
    """
    med_list_str = ", ".join(current_medications) if current_medications else "None reported"

    prompt = (
        "You are an expert geriatric clinical pharmacologist specializing in polypharmacy and elderly care safety.\n\n"
        f"Candidate New Medication: {new_medication}\n"
        f"Patient Current Prescriptions: {med_list_str}\n\n"
        "Analyze potential drug-drug interactions, contraindications, and geriatric vulnerabilities (e.g., Beers Criteria risks, hypotension, falls, renal clearance).\n"
        "Strictly return ONLY a valid JSON object with these exact keys:\n"
        "{\n"
        '  "severity": "safe" | "caution" | "danger",\n'
        '  "summary": "Clear, concise 1-2 sentence medical summary of any known interactions",\n'
        '  "recommendation": "Empathetic, actionable recommendation for the elderly patient and their caregiver"\n'
        "}\n\n"
        "Rules:\n"
        "- If no current medications or no known interaction exists, set severity to 'safe'.\n"
        "- If mild or moderate caution is warranted (e.g., take with food, monitor blood pressure), set severity to 'caution'.\n"
        "- If severe contraindication, toxicity risk, or life-threatening interaction exists, set severity to 'danger'.\n"
        "Do not include markdown formatting or commentary outside the JSON."
    )

    text_output, successful_model = execute_gemini_fallback_prompt(prompt, image=None)

    cleaned_json_str = re.sub(r"^```(?:json)?\s*", "", text_output, flags=re.MULTILINE)
    cleaned_json_str = re.sub(r"```$", "", cleaned_json_str, flags=re.MULTILINE).strip()

    try:
        parsed_data = json.loads(cleaned_json_str)
    except Exception as parse_err:
        logger.error(f"[Interactions] Failed to parse response from {successful_model}: {parse_err}")
        return {
            "severity": "caution",
            "summary": "Interaction analysis completed with inconclusive formatting.",
            "recommendation": "Please consult your prescribing doctor or pharmacist before starting this medication.",
            "raw_response": text_output,
        }

    severity = parsed_data.get("severity", "caution").lower()
    if severity not in ("safe", "caution", "danger"):
        severity = "caution"

    return {
        "severity": severity,
        "summary": parsed_data.get("summary", "No clinical interaction summary available."),
        "recommendation": parsed_data.get(
            "recommendation", "Always verify with your licensed physician or pharmacist."
        ),
        "raw_response": text_output,
    }
