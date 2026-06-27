from fastapi import APIRouter, HTTPException, status
from app.schemas.telemetry import SessionInitRequest, SessionInitResponse, TelemetryPing, TelemetryResponse
from app.services.telemetry_service import TelemetryService

router = APIRouter()

@router.post("/session/start", response_model=SessionInitResponse, status_code=status.HTTP_201_CREATED)
async def start_tracking_session(payload: SessionInitRequest):
    """
    Initializes a highly scalable tracking state. Captures planned path vectors 
    and pins them directly into memory.
    """
    try:
        session_id = await TelemetryService.initialize_session(
            user_id=payload.user_id,
            route_id=payload.route_id,
            safe_path=payload.safe_path
        )
        return SessionInitResponse(session_id=session_id, status="active")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to initialize tracking context: {str(e)}")

@router.post("/ping/{user_id}", response_model=TelemetryResponse)
async def ingest_telemetry(user_id: str, ping: TelemetryPing):
    """
    High-frequency geolocation ingest endpoint. Evaluates distance metrics 
    against cache constraints in micro-seconds.
    """
    is_deviated, distance = await TelemetryService.process_ping(
        user_id=user_id,
        current_lat=ping.latitude,
        current_lon=ping.longitude,
        timestamp=ping.timestamp
    )
    
    # Session verification layer
    session_id = f"track:{user_id}"
    if distance == 0.0 and not is_deviated:
        # Check if 0.0 was returned due to non-existent tracking session
        import redis.asyncio as aioredis
        from app.services.telemetry_service import redis_client
        if not await redis_client.exists(session_id):
            raise HTTPException(status_code=404, detail="Active tracking session not found for this identifier.")

    return TelemetryResponse(
        session_id=session_id,
        is_deviated=is_deviated,
        distance_from_route_meters=round(distance, 2)
    )