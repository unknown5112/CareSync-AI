import os
import traceback
from typing import Any, Dict
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, status, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.utils.ai_scanner import scan_medication_strip

# Load environment variables from .env
load_dotenv()

app = FastAPI(
    title="CareSync AI Backend",
    description="Intelligent Elderly Care & Medication Management Platform API",
    version="1.0.0",
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class HealthCheckResponse(BaseModel):
    status: str
    message: str
    version: str


@app.get("/", response_model=HealthCheckResponse, status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, str]:
    """Health check endpoint to verify backend service status."""
    return {
        "status": "healthy",
        "message": "CareSync AI API is operational",
        "version": "1.0.0",
    }


@app.post("/api/scan-medication", status_code=status.HTTP_200_OK)
async def scan_medication(
    file: UploadFile = File(..., description="Image file of the medication packaging or strip")
) -> Dict[str, Any]:
    """
    Route for medication strip OCR and information extraction using Gemini Vision API.
    Opens image via Pillow and passes image object directly to Gemini.
    """
    try:
        image_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"

        scan_result = scan_medication_strip(image_bytes, mime_type=mime_type)

        return {
            "status": "success",
            "filename": file.filename,
            "data": scan_result,
        }
    except Exception as e:
        print("[POST /api/scan-medication] Exception encountered:")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gemini AI medication scan failed: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
