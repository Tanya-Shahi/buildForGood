import asyncio
from typing import Dict
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.services.dossier_service import DossierService
from app.services.notification_service import NotificationService
from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.models.incident_log import IncidentLog
from app.db.session import SessionLocal

router = APIRouter()

active_escalations: Dict[str, asyncio.Task] = {}

async def start_escalation_countdown(user_id: str) -> bool:
    if user_id in active_escalations:
        return False
        
    async def countdown_task():
        try:
            await asyncio.sleep(10)
            await trigger_sos_escalation(user_id)
        except asyncio.CancelledError:
            print(f"SOS Countdown for {user_id} was successfully aborted.")
        except Exception as e:
            print(f"Escalation failed: {str(e)}")
        finally:
            active_escalations.pop(user_id, None)

    task = asyncio.create_task(countdown_task())
    active_escalations[user_id] = task
    return True

@router.post("/sos/start")
async def trigger_manual_sos_route(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user_id_str = str(user.id)
    started = await start_escalation_countdown(user_id_str)
    
    if not started:
        return {"status": "ALREADY_ARMED", "message": "Countdown is already running."}
        
    return {"status": "COUNTDOWN_STARTED", "seconds_remaining": 10}


@router.post("/sos/cancel")
async def cancel_escalation(
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user)
):
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user_id_str = str(user.id)
    task = active_escalations.get(user_id_str)
    if task:
        task.cancel()
        return {"status": "CANCELLED", "message": "SOS system disarmed."}
    return {"status": "IGNORED", "message": "No active countdown found for user."}

async def trigger_sos_escalation(user_id: str):
    """The real deal. Fires off the dossier and notifications."""
    dossier = await DossierService.compile_emergency_dossier(user_id)
    if "error" in dossier:
        print(f"Failed to compile dossier: {dossier['error']}")
        return
        
    # 🔥 FIX (Bug 2.1): Only archive if real coordinates exist
    db = SessionLocal()
    try:
        lat = dossier.get("last_known_location", {}).get("lat")
        lon = dossier.get("last_known_location", {}).get("lon")
        
        if lat is None or lon is None:
            print(f"⚠️ WARNING: Skipping auto-archive for {dossier['incident_id']}. No GPS history available.")
        else:
            new_log = IncidentLog(
                incident_id=dossier["incident_id"],
                user_id=dossier["user_id"],
                latitude=lat,
                longitude=lon,
                geom=f"SRID=4326;POINT({lon} {lat})",
                evidence_payload=dossier
            )
            db.add(new_log)
            db.commit()
            print(f"✅ Dossier securely archived for incident {dossier['incident_id']}")
    finally:
        db.close()
        
    await NotificationService.send_emergency_alerts(dossier)
    print(f"🚨 CRITICAL SOS DISPATCHED FOR {user_id} 🚨")