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
    Opens the image using Pillow (PIL.Image) before sending it to Gemini.
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

        # In google-generativeai==0.3.1, gemini-pro-vision is the supported multimodal vision model name
        # We can also attempt gemini-1.5-flash if available on the account
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
        except Exception:
            model = genai.GenerativeModel("gemini-pro-vision")

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
            response = model.generate_content([prompt, img])
        except Exception as model_err:
            # If 1.5-flash fails on older library version, fallback to gemini-pro-vision
            print(f"[AI Scanner] Primary vision call error: {model_err}. Retrying with gemini-pro-vision...")
            fallback_model = genai.GenerativeModel("gemini-pro-vision")
            response = fallback_model.generate_content([prompt, img])

        if not response or not hasattr(response, "text") or not response.text:
            raise RuntimeError("Gemini API returned an empty or invalid response.")

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
