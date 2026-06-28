from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.api import deps
from app.api.deps import get_current_user
from app.models.incident_log import IncidentLog
from app.services.ml_feedback_service import MLFeedbackService
from datetime import datetime

router = APIRouter()

@router.post("/archive")
async def archive_sos_dossier(
    dossier: dict, 
    db: Session = Depends(deps.get_db),
    current_user: str = Depends(get_current_user) 
):
    """Saves the JSON permanently to PostgreSQL."""
    loc = dossier.get("last_known_location")
    if not loc or "lat" not in loc or "lon" not in loc:
        raise HTTPException(
            status_code=400, 
            detail="Cannot archive SOS dossier: Missing location coordinates."
        )
        
    lat, lon = loc["lat"], loc["lon"]
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
async def verify_incident_and_learn(
    incident_id: str, 
    background_tasks: BackgroundTasks, 
    db: Session = Depends(deps.get_db),
    current_user: str = Depends(get_current_user) 
):
    incident = db.query(IncidentLog).filter(IncidentLog.incident_id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incident not found")
        
    if incident.is_verified:
        return {"message": "Incident already verified."}
        
    incident.is_verified = True
    
    # Offload the heavy model training to the background
    current_hour = datetime.utcnow().hour
    background_tasks.add_task(
        MLFeedbackService.integrate_verified_incident,
        lat=incident.latitude, 
        lon=incident.longitude, 
        time_of_day_hour=current_hour
    )
    
    incident.ml_integrated = True 
    db.commit()
    
    return {
        "status": "Verified", 
        "message": "Incident verified. AI model retraining queued in background."
    }

# ---------------------------------------------------------
# 🔥 NEW: NGO DASHBOARD ROUTE
# ---------------------------------------------------------
@router.get("/dashboard/sos-events")
async def fetch_ngo_dashboard_events(
    limit: int = 50,
    db: Session = Depends(deps.get_db),
    current_user: str = Depends(get_current_user)
):
    """
    [P1] Tier-2 Responder Dashboard: Fetches all escalated SOS events 
    for NGOs/Police to view on a map and take action.
    """
    # Fetch logs ordered by the most recent emergency first
    logs = db.query(IncidentLog).order_by(IncidentLog.created_at.desc()).limit(limit).all()
    
    return [
        {
            "incident_id": log.incident_id,
            "user_id": log.user_id,
            "latitude": log.latitude,
            "longitude": log.longitude,
            "is_verified": log.is_verified,
            "ml_integrated": log.ml_integrated,
            "timestamp": log.created_at,
            "evidence_dossier": log.evidence_payload 
        }
        for log in logs
    ]