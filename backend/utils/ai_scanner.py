import json
import os
import re
from typing import Any, Dict, Union
import google.generativeai as genai
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()


def get_gemini_client():
    """Configures and validates the Google Gemini API client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY environment variable is missing. "
            "Please configure GEMINI_API_KEY in your environment or .env file."
        )
    genai.configure(api_key=api_key)


def scan_medication_strip(
    image_data: Union[bytes, str], mime_type: str = "image/jpeg"
) -> Dict[str, Any]:
    """
    Extracts medication name, suggested dosage, and essential details
    from an image of a medication strip or packaging using the Gemini Vision API.

    Args:
        image_data: Raw image bytes or local file path to the medication image.
        mime_type: MIME type of the image (e.g., 'image/jpeg', 'image/png').

    Returns:
        A clean dictionary containing real extracted medication details.

    Raises:
        ValueError, RuntimeError, or Exception if the API key is absent,
        the model fails, or response cannot be parsed.
    """
    get_gemini_client()

    # Model for vision/multimodal extraction
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Prepare image payload
    if isinstance(image_data, str):
        with open(image_data, "rb") as f:
            image_bytes = f.read()
    elif isinstance(image_data, bytes):
        image_bytes = image_data
    else:
        raise TypeError("image_data must be bytes or a valid file path string.")

    if not image_bytes:
        raise ValueError("Provided image data is empty.")

    image_part = {
        "mime_type": mime_type,
        "data": image_bytes,
    }

    prompt = (
        "You are an expert medical AI assistant specialized in reading medication packaging, strips, and prescription bottles. "
        "Analyze this medication image carefully.\n\n"
        "Extract the information and strictly return ONLY a valid JSON object with these exact keys:\n"
        "{\n"
        '  "medication_name": "Exact brand and generic chemical name of the medicine",\n'
        '  "suggested_dosage": "Dosage instructions or strength stated on the packaging",\n'
        '  "strength": "Concentration per tablet/capsule (e.g., 500mg, 10mg) if visible",\n'
        '  "instructions": "Any visible instructions, precautions, or warnings",\n'
        '  "confidence": "high, medium, or low"\n'
        "}\n\n"
        "Do not include markdown blocks, introductory words, or explanations outside the JSON."
    )

    try:
        response = model.generate_content([prompt, image_part])
    except Exception as exc:
        raise RuntimeError(f"Gemini API vision processing failed: {str(exc)}") from exc

    if not response or not hasattr(response, "text") or not response.text:
        raise RuntimeError("Gemini API returned an empty or invalid response.")

    text_output = response.text.strip()

    # Clean potential markdown fences
    cleaned_json_str = re.sub(r"^```(?:json)?\s*", "", text_output, flags=re.MULTILINE)
    cleaned_json_str = re.sub(r"```$", "", cleaned_json_str, flags=re.MULTILINE).strip()

    try:
        parsed_data = json.loads(cleaned_json_str)
    except Exception as parse_err:
        raise RuntimeError(
            f"Failed to parse JSON response from Gemini Vision: {str(parse_err)}. Raw text: {text_output}"
        ) from parse_err

    return {
        "medication_name": parsed_data.get("medication_name", "Unknown Medication"),
        "suggested_dosage": parsed_data.get("suggested_dosage", "Consult doctor/pharmacist"),
        "strength": parsed_data.get("strength"),
        "instructions": parsed_data.get("instructions"),
        "confidence": parsed_data.get("confidence", "high"),
        "raw_response": text_output,
    }
