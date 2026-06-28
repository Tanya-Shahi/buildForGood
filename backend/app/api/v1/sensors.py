from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from pydantic import BaseModel
from app.services.fusion_engine import FusionEngine
from app.services.connection_manager import manager
from .escalation import start_escalation_countdown
from app.api.deps import get_current_user  # 🔥 NEW: Auth dependency

router = APIRouter()

# ---------------------------------------------------------
# 1. THE WEBSOCKET LISTENER (React Native connects here)
# ---------------------------------------------------------
@router.websocket("/ws/{user_id}")
async def user_websocket_endpoint(websocket: WebSocket, user_id: str):
    """
    The mobile app opens a connection to this endpoint as soon as the user logs in.
    It stays open silently in the background, waiting for push alerts.
    """
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            print(f"Received message from {user_id}: {data}")
            
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        print(f"User {user_id} disconnected from WebSocket.")


# ---------------------------------------------------------
# 2. THE SENSOR SYNC & TRIGGER (The Fusion Engine)
# ---------------------------------------------------------
class SensorPayload(BaseModel):
    user_id: str
    route_deviation: bool = False
    motion_anomaly: bool = False
    audio_scream: bool = False
    duress_pin: bool = False

@router.post("/sync")
async def sync_device_sensors(
    payload: SensorPayload,
    current_user: str = Depends(get_current_user)  # 🔥 FIX: Endpoint locked down
):
    """
    Ingests high-frequency sensor spikes from the mobile app.
    """
    flags = payload.model_dump(exclude={"user_id"})
    
    is_critical, active_triggers, score = FusionEngine.evaluate_threat(
        user_id=payload.user_id, 
        flags=flags
    )
    
    if is_critical:
        alert_payload = {
            "type": "CRITICAL_ESCALATION_WARNING",
            "message": "Corroborated threat detected. Initiating SOS sequence.",
            "countdown_seconds": 10,
            "active_triggers": active_triggers
        }
        
        await manager.send_personal_alert(alert_payload, payload.user_id)
        print(f"🚨 WEBSOCKET PUSHED: Alert sent to {payload.user_id}'s device.")
        
        await start_escalation_countdown(payload.user_id)

    return {
        "status": "evaluated",
        "threat_score": score,
        "is_escalating": is_critical,
        "active_triggers": active_triggers
    }