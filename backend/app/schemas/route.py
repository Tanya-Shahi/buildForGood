# app/schemas/route.py
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class IncidentCreate(BaseModel):
    category: str = Field(..., description="e.g., harassment, poor_lighting, stalking")
    description: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    # Note: Audio file uploads will be handled via form-data in a separate Gemini endpoint

class IncidentResponse(BaseModel):
    id: int
    category: str
    description: Optional[str]
    latitude: float
    longitude: float
    created_at: datetime
    is_active: bool

    class Config:
        from_attributes = True  # Tells Pydantic to read data from SQLAlchemy models

class TelemetryPing(BaseModel):
    """Payload for the passive route-deviation monitor [P0]"""
    latitude: float
    longitude: float
    speed_mps: Optional[float] = 0.0  # For the motion anomaly detection [P1]