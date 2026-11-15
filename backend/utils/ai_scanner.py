import json
import os
import re
from typing import Any, Dict, Optional, Union
import google.generativeai as genai
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()


def get_gemini_client():
    """Configures and validates the Google Gemini API client."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. Please define it in your environment or .env file."
        )
    genai.configure(api_key=api_key)


def scan_medication_strip(
    image_data: Union[bytes, str], mime_type: str = "image/jpeg"
) -> Dict[str, Any]:
    """
    Extracts medication name, suggested dosage, and essential details
    from an image of a medication strip or packaging using the Gemini API.

    Args:
        image_data: Raw image bytes or local file path to the medication image.
        mime_type: MIME type of the image (e.g., 'image/jpeg', 'image/png').

    Returns:
        A clean dictionary containing extracted medication details:
        {
            "medication_name": str,
            "suggested_dosage": str,
            "strength": Optional[str],
            "instructions": Optional[str],
            "raw_response": Optional[str]
        }
    """
    get_gemini_client()

    # Use gemini-1.5-flash or gemini-pro-vision for multimodal vision tasks
    # In google-generativeai==0.3.1, gemini-pro-vision or gemini-1.5-flash is standard
    model = genai.GenerativeModel("gemini-1.5-flash")

    # Prepare image part
    if isinstance(image_data, str):
        # File path provided
        with open(image_data, "rb") as f:
            image_bytes = f.read()
    elif isinstance(image_data, bytes):
        image_bytes = image_data
    else:
        raise TypeError("image_data must be bytes or a valid file path string.")

    image_part = {
        "mime_type": mime_type,
        "data": image_bytes,
    }

    prompt = (
        "You are an expert medical AI assistant specialized in analyzing medication packaging and strips. "
        "Analyze this image of a medication strip or box carefully.\n\n"
        "Extract the following information and return ONLY a valid JSON object with these exact keys:\n"
        "{\n"
        '  "medication_name": "Brand and generic chemical name of the medicine (or \'Unknown\' if not readable)",\n'
        '  "suggested_dosage": "Dosage recommendations or strength found on the packaging (or \'Consult doctor/pharmacist\')",\n'
        '  "strength": "Concentration per tablet/capsule (e.g., 500mg, 10mg) if visible",\n'
        '  "instructions": "Any visible instructions, warnings, or frequency (or null)",\n'
        '  "confidence": "high, medium, or low"\n'
        "}\n\n"
        "Do not include markdown fences or any explanation outside the JSON."
    )

    response = model.generate_content([prompt, image_part])
    text_output = response.text.strip() if response and response.text else ""

    # Clean potential markdown formatting
    cleaned_json_str = re.sub(r"^```(?:json)?\s*", "", text_output, flags=re.MULTILINE)
    cleaned_json_str = re.sub(r"```$", "", cleaned_json_str, flags=re.MULTILINE).strip()

    try:
        parsed_data = json.loads(cleaned_json_str)
        return {
            "medication_name": parsed_data.get("medication_name", "Unknown"),
            "suggested_dosage": parsed_data.get("suggested_dosage", "Consult doctor/pharmacist"),
            "strength": parsed_data.get("strength"),
            "instructions": parsed_data.get("instructions"),
            "confidence": parsed_data.get("confidence", "medium"),
            "raw_response": text_output,
        }
    except (json.JSONDecodeError, AttributeError):
        # Fallback dictionary if JSON parsing fails
        return {
            "medication_name": "Unknown",
            "suggested_dosage": "Consult doctor/pharmacist",
            "strength": None,
            "instructions": None,
            "confidence": "low",
            "raw_response": text_output,
        }
