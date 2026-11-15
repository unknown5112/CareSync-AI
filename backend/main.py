import functools
import os
import traceback
from typing import Any, Dict
from dotenv import load_dotenv
from fastapi import FastAPI, File, Request, Response, UploadFile, status, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.utils.ai_scanner import scan_medication_strip

# Load environment variables from .env
load_dotenv()


@functools.lru_cache(maxsize=32)
def get_env_var(key: str, default: str = "") -> str:
    """Cached accessor for environment variables to optimize runtime configuration lookup."""
    return os.getenv(key, default)


app = FastAPI(
    title="CareSync AI Backend",
    description="Intelligent Elderly Care & Medication Management Platform API",
    version="1.0.0",
)

# Tightened CORS Middleware with strict allowed methods and headers
ALLOWED_ORIGINS = [
    origin.strip()
    for origin in get_env_var(
        "ALLOWED_ORIGINS",
        "https://caresync-ai-we1r.onrender.com,http://localhost:3000,http://localhost:8000,http://127.0.0.1:8000,http://127.0.0.1:5500",
    ).split(",")
    if origin.strip()
]
# If wildcard is needed for static frontend previews, include it explicitly or use allowed origins
if "*" in ALLOWED_ORIGINS or get_env_var("ALLOW_ALL_ORIGINS", "false").lower() == "true":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
    )


# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforces essential security headers on all outgoing responses."""
    response: Response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


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


# Maximum allowed upload payload size: 5MB
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024


@app.post("/api/scan-medication", status_code=status.HTTP_200_OK)
async def scan_medication(
    file: UploadFile = File(..., description="Image file of the medication packaging or strip")
) -> Dict[str, Any]:
    """
    Route for medication strip OCR and information extraction using Gemini Vision API.
    Enforces payload size limit (<5MB) and offloads blocking AI processing to a threadpool.
    """
    try:
        # Read uploaded image bytes asynchronously
        image_bytes = await file.read()

        # Enforce 5MB upload size limit (HTTP 413 Payload Too Large)
        if len(image_bytes) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Uploaded file exceeds the maximum allowed size limit of 5MB (Received: {len(image_bytes) / (1024 * 1024):.2f}MB).",
            )

        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded image file is empty.",
            )

        mime_type = file.content_type or "image/jpeg"

        # Offload synchronous/blocking Gemini AI vision API call to worker thread pool
        scan_result = await run_in_threadpool(scan_medication_strip, image_bytes, mime_type)

        return {
            "status": "success",
            "filename": file.filename,
            "data": scan_result,
        }
    except HTTPException:
        # Re-raise handled HTTPExceptions directly
        raise
    except Exception as e:
        print("[POST /api/scan-medication] Exception encountered:")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gemini AI medication scan failed: {str(e)}",
        )


if __name__ == "__main__":
    import uvicorn

    port = int(get_env_var("PORT", "8000"))
    uvicorn.run("backend.main:app", host="0.0.0.0", port=port, reload=True)
