import os
import shutil
import tempfile
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement
from sqlalchemy import func

from app.api.deps import get_db, get_current_user, get_current_ngo_user
from app.models.route import Incident
from app.schemas.route import IncidentCreate, IncidentResponse
from app.services.gemini_service import transcribe_incident_audio

# Imports for Trust Engine integration
from app.models.user import User
from app.services.trust_engine import TrustEngine

router = APIRouter()

MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024 

@router.post("/incidents", response_model=IncidentResponse)
def report_incident(
    incident_in: IncidentCreate, 
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)  
):
    point_wkt = f"POINT({incident_in.longitude} {incident_in.latitude})"
    user = db.query(User).filter(User.username == current_user).first()
    
    new_incident = Incident(
        reporter_id=user.id if user else None,  
        category=incident_in.category,
        description=incident_in.description,
        location=WKTElement(point_wkt, srid=4326)
    )
    
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    
    return IncidentResponse(
        id=new_incident.id,
        category=new_incident.category,
        description=new_incident.description,
        latitude=incident_in.latitude,
        longitude=incident_in.longitude,
        created_at=new_incident.created_at,
        is_active=new_incident.is_active
    )

def process_and_transcribe(upload_file: UploadFile, safe_filename: str) -> str:
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(safe_filename)[1]) as tmp:
        shutil.copyfileobj(upload_file.file, tmp)
        temp_path = tmp.name
        
    try:
        return transcribe_incident_audio(temp_path)
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)

@router.post("/incidents/voice", response_model=IncidentResponse)
async def report_incident_with_audio(
    category: str = Form(...),
    description: str = Form(""), 
    latitude: float = Form(...),
    longitude: float = Form(...),
    audio_file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    valid_extensions = ('.wav', '.mp3', '.m4a', '.ogg', '.webm')
    safe_filename = os.path.basename(audio_file.filename)
    
    if not safe_filename.lower().endswith(valid_extensions):
        raise HTTPException(status_code=400, detail="Invalid audio format.")

    if audio_file.size and audio_file.size > MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Max 10MB.")

    transcript = await run_in_threadpool(process_and_transcribe, audio_file, safe_filename)
    final_description = f"{description}\n\n[Voice Transcript]: {transcript}".strip() if transcript else description

    point_wkt = f"POINT({longitude} {latitude})"
    user = db.query(User).filter(User.username == current_user).first()
    
    new_incident = Incident(
        reporter_id=user.id if user else None,  
        category=category,
        description=final_description,
        location=WKTElement(point_wkt, srid=4326)
    )
    
    db.add(new_incident)
    db.commit()
    db.refresh(new_incident)
    
    return IncidentResponse(
        id=new_incident.id,
        category=new_incident.category,
        description=new_incident.description,
        latitude=latitude,
        longitude=longitude,
        created_at=new_incident.created_at,
        is_active=new_incident.is_active
    )

@router.get("/incidents", response_model=list[IncidentResponse])
def get_active_incidents(
    limit: int = 100, 
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)  
):
    records = db.query(
        Incident,
        func.ST_Y(Incident.location).label("lat"),
        func.ST_X(Incident.location).label("lon")
    ).filter(Incident.is_active == True).limit(limit).all()

    return [
        IncidentResponse(
            id=incident.id,
            category=incident.category,
            description=incident.description,
            latitude=lat,
            longitude=lon,
            created_at=incident.created_at,
            is_active=incident.is_active
        )
        for incident, lat, lon in records
    ]

# ---------------------------------------------------------
# NGO / MODERATOR ROUTES (Trust Engine Triggers)
# ---------------------------------------------------------
@router.post("/incidents/{incident_id}/verify")
def verify_community_incident(
    incident_id: int, 
    db: Session = Depends(get_db),
    ngo_user: User = Depends(get_current_ngo_user) 
):
    """[P1] NGO/Moderator verifies an incident. Rewards the reporter."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.reporter_id == ngo_user.id:
        raise HTTPException(status_code=403, detail="You cannot verify your own incident report.")
        
    if incident.reporter_id:
        TrustEngine.reward_user(db, incident.reporter_id)
        
    # 🔥 FIX (Audit Fields): Record the action
    incident.verified_by_id = ngo_user.id
    db.commit()
        
    return {"status": "Verified", "message": "Reporter trust score increased."}

@router.post("/incidents/{incident_id}/false_flag")
def flag_fake_incident(
    incident_id: int, 
    db: Session = Depends(get_db),
    ngo_user: User = Depends(get_current_ngo_user) 
):
    """[P1] NGO/Moderator marks an incident as fake. Penalizes the reporter and removes the pin."""
    incident = db.query(Incident).filter(Incident.id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.reporter_id == ngo_user.id:
        raise HTTPException(status_code=403, detail="You cannot flag your own incident report.")
        
    incident.is_active = False 
    
    # 🔥 FIX (Audit Fields): Record the action
    incident.flagged_by_id = ngo_user.id
    
    if incident.reporter_id:
        TrustEngine.penalize_user(db, incident.reporter_id)
        
    db.commit()
    return {"status": "Removed", "message": "Incident hidden and reporter penalized."}