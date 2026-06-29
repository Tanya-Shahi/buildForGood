from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.api.deps import get_db, get_current_user  
from app.schemas.telemetry import SessionInitRequest, SessionInitResponse, TelemetryPing, TelemetryResponse
from app.services.telemetry_service import TelemetryService
from app.services.connection_manager import manager
from app.services.telemetry_service import redis_client 
from app.models.user import User

router = APIRouter()

@router.post("/session/start", response_model=SessionInitResponse, status_code=status.HTTP_201_CREATED)
async def start_tracking_session(
    payload: SessionInitRequest,
    db: Session = Depends(get_db),
    current_user: str = Depends(get_current_user) 
):
    """Initializes a highly scalable tracking state."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    try:
        session_id = await TelemetryService.initialize_session(
            user_id=str(user.id), # 🔥 BOLA FIXED
            route_id=payload.route_id,
            safe_path=payload.safe_path
        )
        return SessionInitResponse(session_id=session_id, status="active")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize tracking context: {str(e)}")

# 🔥 BOLA FIXED: Removed {user_id} from the path route
@router.post("/ping", response_model=TelemetryResponse)
async def ingest_telemetry(
    ping: TelemetryPing,
    db: Session = Depends(get_db), 
    current_user: str = Depends(get_current_user) 
):
    """High-frequency geolocation ingest endpoint."""
    user = db.query(User).filter(User.username == current_user).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    user_id_str = str(user.id)
    
    is_deviated, distance = await TelemetryService.process_ping(
        db=db,
        user_id=user_id_str, # 🔥 BOLA FIXED
        current_lat=ping.latitude,
        current_lon=ping.longitude,
        timestamp=ping.timestamp
    )
    
    session_id = f"track:{user_id_str}"
    
    # The WebSocket Alert Trigger
    if is_deviated:
        alert_payload = {
            "type": "ROUTE_DEVIATION_ALERT",
            "session_id": session_id,
            "distance_meters": round(distance, 2),
            "message": "Deviation detected. Triggering confirmation window."
        }
        await manager.send_personal_alert(alert_payload, user_id_str)

    # Check for missing session
    if distance == 0.0 and not is_deviated:
        if not await redis_client.exists(session_id):
            raise HTTPException(status_code=404, detail="Active tracking session not found.")
            
    return TelemetryResponse(
        session_id=session_id,
        is_deviated=is_deviated,
        distance_from_route_meters=round(distance, 2)
    )