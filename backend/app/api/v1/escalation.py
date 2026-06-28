import asyncio
from typing import Dict
from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from app.services.dossier_service import DossierService
from app.services.notification_service import NotificationService
from app.api.deps import get_current_user  # 🔥 NEW: Auth dependency

router = APIRouter()

# Global dictionary to hold active countdown timers in memory
active_escalations: Dict[str, asyncio.Task] = {}

@router.post("/sos/start/{user_id}")
async def start_escalation_countdown(
    user_id: str,
    current_user: str = Depends(get_current_user)  # 🔥 FIX: Endpoint locked down
):
    """
    Called by the Fusion Engine. Starts the 10-second countdown.
    If not cancelled in time, it fires the true SOS.
    """
    if user_id in active_escalations:
        return {"status": "ALREADY_ARMED", "message": "Countdown is already running."}
        
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
    
    return {"status": "COUNTDOWN_STARTED", "seconds_remaining": 10}

@router.post("/sos/cancel/{user_id}")
async def cancel_escalation(
    user_id: str,
    current_user: str = Depends(get_current_user)  # 🔥 FIX: Endpoint locked down
):
    """Hits the brakes on the countdown if it's a false alarm."""
    task = active_escalations.get(user_id)
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
        
    await NotificationService.send_emergency_alerts(dossier)
    print(f"🚨 CRITICAL SOS DISPATCHED FOR {user_id} 🚨")