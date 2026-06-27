from fastapi import APIRouter
from pydantic import BaseModel
from app.services.fusion_engine import FusionEngine

router = APIRouter()

# The payload schema expected from the mobile device
class SensorPayload(BaseModel):
    user_id: str
    route_deviation: bool = False
    motion_anomaly: bool = False
    audio_scream: bool = False
    duress_pin: bool = False

@router.post("/sync")
async def sync_device_sensors(payload: SensorPayload):
    """
    Ingests high-frequency sensor spikes from the mobile app, passes them to 
    the Fusion Engine, and triggers WebSockets if a multi-sensor threat is detected.
    """
    # Convert Pydantic model to a dictionary, excluding the user_id so 
    # we only pass the boolean sensor flags to the engine.
    flags = payload.model_dump(exclude={"user_id"})
    
    is_critical, active_triggers, score = FusionEngine.evaluate_threat(
        user_id=payload.user_id, 
        flags=flags
    )
    
    if is_critical:
        # TODO: Trigger your WebSocket connection here to push the 10-second 
        # confirmation/cancel window down to the user's screen.
        print(f"🚨 WEBSOCKET TRIGGER: Sending confirmation window to {payload.user_id}")

    return {
        "status": "evaluated",
        "threat_score": score,
        "is_escalating": is_critical,
        "active_triggers": active_triggers
    }