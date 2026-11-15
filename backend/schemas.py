"""Pydantic v2 schemas for CareSync AI API request and response validation."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Schema for health and readiness check endpoint."""

    status: str = Field(..., description="Overall service status (healthy or degraded)")
    message: str = Field(..., description="Descriptive status message")
    version: str = Field(..., description="Service version")
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="Readiness status of external dependencies (e.g., gemini, supabase)",
    )


class MedicationScanData(BaseModel):
    """Extracted medication information schema."""

    medication_name: str = Field(..., description="Brand or generic medication name")
    suggested_dosage: str = Field(..., description="Recommended dosage and intake schedule")
    strength: Optional[str] = Field(None, description="Active ingredient concentration")
    instructions: Optional[str] = Field(None, description="Special instructions or precautions")
    confidence: Literal["high", "medium", "low"] = Field("high", description="OCR confidence rating")
    raw_response: Optional[str] = Field(None, description="Raw model text output")
    from_cache: bool = Field(False, description="Indicates whether result was served from LRU cache")


class ScanMedicationResponse(BaseModel):
    """Response payload for medication scan endpoint."""

    status: str = Field("success", description="Status string")
    filename: str = Field(..., description="Name of the analyzed image file")
    data: MedicationScanData = Field(..., description="Extracted clinical details")


class DrugInteractionRequest(BaseModel):
    """Request payload for geriatric drug interaction screening."""

    new_medication: str = Field(..., min_length=2, description="Candidate new medication name")
    current_medications: List[str] = Field(..., description="List of medications currently taken by senior")


class DrugInteractionResponse(BaseModel):
    """Response payload for geriatric drug interaction analysis."""

    severity: Literal["safe", "caution", "danger"] = Field(
        ..., description="Clinical risk rating for the senior patient"
    )
    summary: str = Field(..., description="Clinical summary of the interaction mechanism")
    recommendation: str = Field(..., description="Actionable recommendation for patient and caregiver")
    raw_response: Optional[str] = Field(None, description="Raw AI output")


class CaregiverAlertRequest(BaseModel):
    """Request payload for dispatching emergency/adherence alerts to caregivers."""

    caregiver_email: str = Field(
        ...,
        pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        description="Recipient email of the primary caregiver",
    )
    patient_name: str = Field(..., min_length=1, description="Full name of the elderly patient")
    alert_type: Literal["missed_dose", "sos"] = Field(
        ..., description="Classification of the alert: missed_dose or urgent sos"
    )
    details: str = Field(..., min_length=3, description="Specific context, medication, or situation details")


class CaregiverAlertResponse(BaseModel):
    """Response payload for caregiver alert dispatch."""

    status: str = Field(..., description="Delivery status (success or error)")
    message: str = Field(..., description="Descriptive status confirmation")
    alert_type: str = Field(..., description="Type of alert processed")
