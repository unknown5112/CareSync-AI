import os
from typing import Any, Dict
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

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
    Skeleton route for medication strip OCR and information extraction.
    Will process medication strip images using the Gemini AI scanner module.
    """
    return {
        "status": "success",
        "message": "Medication scan endpoint skeleton ready",
        "filename": file.filename,
        "content_type": file.content_type,
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", 8000))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
