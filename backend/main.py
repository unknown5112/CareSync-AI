"""CareSync AI: Principal Backend Application with Enterprise Security and High Efficiency."""

import traceback
from typing import Any, Dict
from fastapi import FastAPI, File, UploadFile, status, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware

from backend.core.config import get_settings
from backend.core.logging import logger
from backend.core.rate_limiter import SlidingWindowRateLimiter
from backend.core.security_headers import SecurityHeadersMiddleware
from backend.schemas import (
    CaregiverAlertRequest,
    CaregiverAlertResponse,
    DrugInteractionRequest,
    DrugInteractionResponse,
    HealthResponse,
    ScanMedicationResponse,
)
from backend.utils.ai_scanner import analyze_drug_interactions, scan_medication_strip
from backend.utils.email_service import send_caregiver_alert_email

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    description="Enterprise Elderly Care & Medication Management Platform API",
    version=settings.app_version,
)

# 1. GZip Compression Middleware (minimum size 500 bytes)
app.add_middleware(GZipMiddleware, minimum_size=500)

# 2. Strict CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_origin_regex=settings.allowed_origin_regex,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "Accept", "X-Requested-With"],
)

# 3. Pure ASGI Sliding Window Rate Limiting (30 RPM per IP on /api/*)
app.add_middleware(SlidingWindowRateLimiter, requests_per_minute=settings.rate_limit_rpm)

# 4. Pure ASGI Enterprise Security Headers Middleware
app.add_middleware(SecurityHeadersMiddleware)


# Allowed MIME types for medication scanning
ALLOWED_IMAGE_MIMES = {"image/jpeg", "image/png", "image/webp"}


@app.get("/", response_model=HealthResponse, status_code=status.HTTP_200_OK)
@app.get("/health", response_model=HealthResponse, status_code=status.HTTP_200_OK)
async def health_check() -> HealthResponse:
    """Service readiness and health verification endpoint.

    Strictly non-blocking: checks only local configuration readiness, zero network I/O.
    """
    gemini_ready = bool(settings.gemini_api_key)
    supabase_ready = bool(settings.supabase_url and settings.supabase_anon_key)

    dependencies = {
        "gemini_api": "ready" if gemini_ready else "not_configured",
        "supabase_database": "ready" if supabase_ready else "not_configured",
        "email_service": "ready" if settings.email_sender else "simulated",
    }

    return HealthResponse(
        status="healthy",
        message="CareSync AI API is fully operational",
        version=settings.app_version,
        dependencies=dependencies,
    )


@app.post(
    "/api/scan-medication",
    response_model=ScanMedicationResponse,
    status_code=status.HTTP_200_OK,
)
async def scan_medication(
    file: UploadFile = File(..., description="High-resolution image of medication packaging or strip")
) -> ScanMedicationResponse:
    """Extracts medication name, dosage, and warnings from an image using Gemini Vision AI.

    Features SHA-256 caching, PIL integrity verification, downsampling, and threadpool offloading.
    """
    try:
        # Validate MIME type (415 Unsupported Media Type)
        content_type = file.content_type or ""
        if content_type.lower() not in ALLOWED_IMAGE_MIMES:
            raise HTTPException(
                status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                detail=f"Unsupported file format '{content_type}'. Allowed types: {', '.join(sorted(ALLOWED_IMAGE_MIMES))}",
            )

        # Read file asynchronously
        image_bytes = await file.read()

        # Enforce file size limit (413 Payload Too Large)
        if len(image_bytes) > settings.max_file_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"Uploaded file exceeds maximum allowed limit of 5MB ({len(image_bytes)/(1024*1024):.2f}MB received).",
            )

        # Reject empty payload
        if not image_bytes:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Uploaded image payload is empty.",
            )

        # Offload image processing & Gemini OCR to worker threadpool
        scan_result = await run_in_threadpool(scan_medication_strip, image_bytes, content_type)

        return ScanMedicationResponse(
            status="success",
            filename=file.filename or "medication_strip.jpg",
            data=scan_result,
        )

    except HTTPException:
        raise
    except ValueError as ve:
        # Image integrity failure or corrupted image
        logger.warning(f"[ScanMedication] Image validation error: {ve}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid or corrupt image file: {str(ve)}",
        )
    except Exception as exc:
        logger.error(f"[ScanMedication] Unhandled error during scan: {exc}")
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Gemini AI medication scan failed: {str(exc)}",
        )


@app.post(
    "/api/check-interactions",
    response_model=DrugInteractionResponse,
    status_code=status.HTTP_200_OK,
)
async def check_interactions(payload: DrugInteractionRequest) -> DrugInteractionResponse:
    """Analyzes drug-drug interactions for elderly patients using the Gemini fallback sequence."""
    try:
        interaction_result = await run_in_threadpool(
            analyze_drug_interactions,
            payload.new_medication,
            payload.current_medications,
        )
        return DrugInteractionResponse(**interaction_result)
    except Exception as exc:
        logger.error(f"[CheckInteractions] Error analyzing interactions: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Drug interaction analysis failed: {str(exc)}",
        )


@app.post(
    "/api/caregiver-alert",
    response_model=CaregiverAlertResponse,
    status_code=status.HTTP_200_OK,
)
async def caregiver_alert(payload: CaregiverAlertRequest) -> CaregiverAlertResponse:
    """Dispatches an urgent caregiver notification email regarding a senior patient."""
    try:
        email_result = await run_in_threadpool(
            send_caregiver_alert_email,
            str(payload.caregiver_email),
            payload.patient_name,
            payload.alert_type,
            payload.details,
        )
        return CaregiverAlertResponse(
            status=email_result.get("status", "success"),
            message=email_result.get("message", "Alert dispatched"),
            alert_type=payload.alert_type,
        )
    except Exception as exc:
        logger.error(f"[CaregiverAlert] Error sending alert: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Caregiver alert dispatch failed: {str(exc)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=settings.port, reload=settings.debug)
