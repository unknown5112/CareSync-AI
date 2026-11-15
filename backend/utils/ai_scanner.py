import functools
import io
import json
import os
import re
import traceback
from typing import Any, Dict, Union
import google.generativeai as genai
from dotenv import load_dotenv
from PIL import Image

# Ensure environment variables are loaded
load_dotenv()


@functools.lru_cache(maxsize=16)
def get_cached_gemini_api_key() -> str:
    """Cached accessor for GEMINI_API_KEY to eliminate redundant environment lookups."""
    api_key = os.getenv("GEMINI_API_KEY", "")
    return api_key


def get_gemini_client():
    """Configures and validates the Google Gemini API client."""
    api_key = get_cached_gemini_api_key()
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
    from an image of a medication strip or packaging using a sequence of Gemini models.
    Opens the image using Pillow (PIL.Image) and iterates through fallback models.
    """
    try:
        get_gemini_client()

        # Open image using Pillow
        if isinstance(image_data, bytes):
            img = Image.open(io.BytesIO(image_data))
        elif isinstance(image_data, str):
            img = Image.open(image_data)
        else:
            raise TypeError("image_data must be bytes or a valid file path string.")

        # Convert palette/RGBA modes to RGB if needed
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")

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

        # Fallback sequence of models
        models_to_try = [
            'gemini-3.1-flash-lite',
            'gemini-3.7-flash',
            'gemini-omni-flash-preview',
            'gemini-3.8-flash',
        ]

        response = None
        last_exception = None

        for model_name in models_to_try:
            try:
                print(f"[AI Scanner] Attempting vision generation with model: {model_name}")
                model = genai.GenerativeModel(model_name)
                response = model.generate_content([prompt, img])
                if response and hasattr(response, "text") and response.text:
                    print(f"[AI Scanner] Success with model: {model_name}")
                    break
            except Exception as err:
                err_str = str(err).lower()
                last_exception = err
                print(f"[AI Scanner] Model {model_name} failed: {err}")
                # If it's a 404, not found, or unsupported model error, continue to next model
                if "404" in err_str or "not found" in err_str or "notfound" in err_str:
                    continue
                else:
                    # Continue trying the user-specified sequence
                    continue

        if not response or not hasattr(response, "text") or not response.text:
            if last_exception:
                raise RuntimeError(
                    f"All Gemini models in fallback sequence failed. Last error: {str(last_exception)}"
                ) from last_exception
            raise RuntimeError("Gemini API returned an empty or invalid response from all models.")

        text_output = response.text.strip()

        # Clean potential markdown fences
        cleaned_json_str = re.sub(r"^```(?:json)?\s*", "", text_output, flags=re.MULTILINE)
        cleaned_json_str = re.sub(r"```$", "", cleaned_json_str, flags=re.MULTILINE).strip()

        parsed_data = json.loads(cleaned_json_str)

        return {
            "medication_name": parsed_data.get("medication_name", "Unknown Medication"),
            "suggested_dosage": parsed_data.get("suggested_dosage", "Consult doctor/pharmacist"),
            "strength": parsed_data.get("strength"),
            "instructions": parsed_data.get("instructions"),
            "confidence": parsed_data.get("confidence", "high"),
            "raw_response": text_output,
        }

    except Exception as exc:
        print("[AI Scanner] Error in scan_medication_strip:")
        traceback.print_exc()
        raise RuntimeError(str(exc)) from exc
