from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app.models.incident_log import IncidentLog
from app.services.ml_feedback_service import MLFeedbackService
from datetime import datetime

router = APIRouter()

@router.post("/archive")
async def archive_sos_dossier(dossier: dict, db: Session = Depends(deps.get_db)):
    """
    Called internally after an SOS fires. Saves the JSON permanently to PostgreSQL.
    This establishes the bridge so Module 2 (Legal Companion) can fetch it later.
    """
    lat = dossier["last_known_location"]["lat"]
    lon = dossier["last_known_location"]["lon"]
    
    # Create the PostGIS POINT geometry
    geom_point = f"SRID=4326;POINT({lon} {lat})"
    
    new_log = IncidentLog(
        incident_id=dossier["incident_id"],
        user_id=dossier["user_id"],
        latitude=lat,
        longitude=lon,
        geom=geom_point,
        evidence_payload=dossier
    )
    db.add(new_log)
    db.commit()
    return {"status": "Archived permanently to PostgreSQL"}

@router.post("/verify/{incident_id}")
async def verify_incident_and_learn(incident_id: str, db: Session = Depends(deps.get_db)):
    """
    [Tier 2 Dashboard] Called when an NGO verifies the incident.
    Flips the status and triggers the ML Auto-Learner loop.
    """
    incident = db.query(IncidentLog).filter(IncidentLog.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.is_verified:
        return {"message": "Incident already verified."}
        
    # 1. Mark as verified
    incident.is_verified = True
    
    # 2. Trigger ML Auto-Learner
    current_hour = datetime.utcnow().hour
    success = MLFeedbackService.integrate_verified_incident(
        lat=incident.latitude, 
        lon=incident.longitude, 
        time_of_day_hour=current_hour
    )
    
    if success:
        incident.ml_integrated = True
        
    db.commit()
    return {"status": "Verified", "ml_updated": success}