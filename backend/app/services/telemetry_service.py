import json
import math
from typing import List, Tuple
import redis.asyncio as aioredis
from app.core.config import settings

# Initialize the async Redis client using your configuration
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

DEVIATION_THRESHOLD_METERS = 100.0  # Alert if the user wanders more than 100m from path
SESSION_TTL_SECONDS = 86400         # Automatically expire tracking data after 24 hours

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculates the great-circle distance between two points on the Earth's surface in meters.
    """
    R = 6371000.0  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = math.sin(delta_phi / 2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

class TelemetryService:
    @staticmethod
    async def initialize_session(user_id: str, route_id: str, safe_path: List[Tuple[float, float]]) -> str:
        """
        Creates an active tracking session. Storing the baseline path as an in-memory 
        JSON string avoids costly database lookups during runtime telemetry pings.
        """
        session_id = f"track:{user_id}"
        
        session_data = {
            "user_id": user_id,
            "route_id": route_id,
            "safe_path": json.dumps(safe_path),
            "is_deviated": "false"
        }
        
        # Use a pipeline to ensure atomic execution and set the TTL
        async with redis_client.pipeline(transaction=True) as pipe:
            await pipe.hset(session_id, mapping=session_data)
            await pipe.expire(session_id, SESSION_TTL_SECONDS)
            await pipe.execute()
            
        return session_id

    @staticmethod
    async def process_ping(user_id: str, current_lat: float, current_lon: float, timestamp: float) -> Tuple[bool, float]:
        """
        Ingests a rapid GPS coordinate payload, tracks history, and evaluates path adherence.
        """
        session_id = f"track:{user_id}"
        history_key = f"history:{user_id}"
        
        # Pull metadata and path geometry simultaneously from Redis cache
        session_exists = await redis_client.exists(session_id)
        if not session_exists:
            return False, 0.0

        raw_path = await redis_client.hget(session_id, "safe_path")
        safe_path: List[List[float]] = json.loads(raw_path)

        # Find the minimum distance between current position and any point on the designated path
        min_distance = float('inf')
        for point in safe_path:
            path_lat, path_lon = point[0], point[1]
            dist = haversine_distance(current_lat, current_lon, path_lat, path_lon)
            if dist < min_distance:
                min_distance = dist

        is_deviated = min_distance > DEVIATION_THRESHOLD_METERS
        
        # Log breadcrumb history and update status asynchronously via Pipeline
        breadcrumb = json.dumps({"lat": current_lat, "lon": current_lon, "t": timestamp})
        
        async with redis_client.pipeline(transaction=True) as pipe:
            # Append position onto a time-series Redis List for audit trails/frontend mapping
            await pipe.rpush(history_key, breadcrumb)
            await pipe.expire(history_key, SESSION_TTL_SECONDS)
            # Update current deviation flag inside state hash
            await pipe.hset(session_id, "is_deviated", str(is_deviated).lower())
            await pipe.execute()

        return is_deviated, min_distance