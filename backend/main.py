import os
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
    allow_origins=["*"],  # Adjust in production as needed
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
    Route for medication strip OCR and information extraction using Gemini AI.
    """
    try:
        image_bytes = await file.read()
        mime_type = file.content_type or "image/jpeg"

        # Check if GEMINI_API_KEY is configured
        if os.getenv("GEMINI_API_KEY"):
            scan_result = scan_medication_strip(image_bytes, mime_type=mime_type)
        else:
            # Informative fallback if key has not been added yet in local development
            scan_result = {
                "medication_name": "Atorvastatin Calcium (Demo)",
                "suggested_dosage": "1 tablet daily at bedtime (10mg)",
                "strength": "10 mg",
                "instructions": "Take with water after dinner. Demo response - configure GEMINI_API_KEY in .env for live AI extraction.",
                "confidence": "high",
            }

        return {
            "status": "success",
            "filename": file.filename,
            "data": scan_result,
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error processing medication scan: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
