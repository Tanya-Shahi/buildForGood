import os
import shutil
import tempfile
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Depends
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from sqlalchemy import func, cast
from geoalchemy2.types import Geography
from geoalchemy2.elements import WKTElement

from app.services.gemini_service import process_incident_audio
from app.schemas.legal import ComplaintDraftResponse
from app.api.deps import get_current_user, get_db
from app.models.shelter import Shelter
from app.models.incident_log import IncidentLog

router = APIRouter()
logger = logging.getLogger("LegalIntake")

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 

# ---------------------------------------------------------
# 1. RIGHTS EXPLAINER
# ---------------------------------------------------------
@router.get("/rights")
def get_rights_explainer():
    """[P0] Plain-language summary of relevant DV laws and rights."""
    return {
        "laws": [
            {"title": "Protection of Women from Domestic Violence Act, 2005", "summary": "Protects you from physical, emotional, and economic abuse. You have the right to reside in your shared household."},
            {"title": "Zero FIR", "summary": "You can file an FIR at ANY police station, regardless of where the incident occurred. The police must register it and transfer it later."}
        ],
        "next_steps": ["Ensure your physical safety first.", "Keep copies of medical records and the AWAAZ evidence log.", "Contact a nearby shelter for legal counsel."]
    }

# ---------------------------------------------------------
# 2. VOICE INTAKE & COMPLAINT GENERATION
# ---------------------------------------------------------
def save_and_process_audio(upload_file: UploadFile, safe_filename: str, dossier_data: dict = None) -> dict:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(safe_filename)[1]) as tmp:
        shutil.copyfileobj(upload_file.file, tmp)
        temp_path = tmp.name
        
    try:
        return process_incident_audio(temp_path, dossier_data)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/intake", response_model=ComplaintDraftResponse)
async def voice_intake(
    file: UploadFile = File(...),
    incident_id: Optional[str] = Form(None), # 🔥 FIX: Optional auto-import bridge
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)  
):
    """[P0] Voice-based intake, optionally fortified with an AWAAZ SOS dossier."""
    valid_extensions = ('.wav', '.mp3', '.m4a', '.ogg', '.webm')
    safe_filename = os.path.basename(file.filename)
    
    if not safe_filename.lower().endswith(valid_extensions):
        raise HTTPException(status_code=400, detail="Invalid audio format.")
    if file.size and file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File too large.")

    # Fetch the dossier if they arrived via the SOS escalation bridge
    dossier_data = None
    if incident_id:
        log = db.query(IncidentLog).filter(IncidentLog.incident_id == incident_id).first()
        if log:
            dossier_data = log.evidence_payload

    try:
        result = await run_in_threadpool(save_and_process_audio, file, safe_filename, dossier_data)
        return result
    except Exception as e:
        logger.error(f"Voice intake failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal error processing audio.")

# ---------------------------------------------------------
# 3. SHELTER / NGO DIRECTORY
# ---------------------------------------------------------
@router.get("/shelters")
def get_nearby_shelters(
    latitude: float,
    longitude: float,
    radius_km: float = 15.0, 
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    """[P0] Module 2: Fetches curated NGOs/Shelters near the user."""
    point_wkt = f"POINT({longitude} {latitude})"
    radius_meters = radius_km * 1000

    query = db.query(
        Shelter,
        func.ST_Distance(
            cast(Shelter.location, Geography),
            cast(WKTElement(point_wkt, srid=4326), Geography)
        ).label("distance")
    ).filter(
        func.ST_DWithin(
            cast(Shelter.location, Geography),
            cast(WKTElement(point_wkt, srid=4326), Geography),
            radius_meters
        )
    ).order_by("distance").limit(15).all()

    return [
        {
            "id": shelter.id,
            "name": shelter.name,
            "type": shelter.organization_type,
            "phone": shelter.phone_number,
            "address": shelter.address,
            "distance_km": round(distance / 1000, 2)
        }
        for shelter, distance in query
    ]