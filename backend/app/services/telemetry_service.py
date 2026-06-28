import json
from typing import List, Tuple
import redis.asyncio as aioredis
from sqlalchemy.orm import Session
from sqlalchemy import text
from fastapi.concurrency import run_in_threadpool
from app.core.config import settings

# Initialize the async Redis client using your configuration
redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=True)

DEVIATION_THRESHOLD_METERS = 100.0  # Alert if the user wanders more than 100m from path
SESSION_TTL_SECONDS = 86400         # Automatically expire tracking data after 24 hours

class TelemetryService:
    @staticmethod
    async def initialize_session(user_id: str, route_id: str, safe_path: List[Tuple[float, float]]) -> str:
        session_id = f"track:{user_id}"
        
        # 🔥 FIX (Bug 3.3): Instead of a JSON array, map to a PostGIS LINESTRING
        # Note: safe_path contains (lat, lon), but PostGIS requires (lon lat)
        coords = [f"{lon} {lat}" for lat, lon in safe_path]
        linestring_wkt = f"LINESTRING({','.join(coords)})"
        
        async with redis_client.pipeline(transaction=True) as pipe:
            await pipe.hset(session_id, mapping={
                "route_id": route_id,
                "status": "active",
                "safe_path_wkt": linestring_wkt, # Storing the spatial geometry
                "is_deviated": "False"
            })
            await pipe.expire(session_id, SESSION_TTL_SECONDS)
            await pipe.execute()
            
        return session_id

    @staticmethod
    async def process_ping(db: Session, user_id: str, current_lat: float, current_lon: float, timestamp: float) -> Tuple[bool, float]:
        session_id = f"track:{user_id}"
        history_key = f"history:{user_id}"
        
        session_exists = await redis_client.exists(session_id)
        if not session_exists:
            return False, 0.0

        linestring_wkt = await redis_client.hget(session_id, "safe_path_wkt")
        if not linestring_wkt:
            return False, 0.0

        # 🔥 FIX (Bug 3.3): Delegate the math to PostGIS using ST_Distance!
        point_wkt = f"POINT({current_lon} {current_lat})"
        
        # Use PostGIS Geography cast for accurate meter-based distances on the globe
        query = text("""
            SELECT ST_Distance(
                ST_GeomFromText(:point, 4326)::geography, 
                ST_GeomFromText(:line, 4326)::geography
            )
        """)
        
        # Run the synchronous SQLAlchemy call in a threadpool so we don't freeze the async server
        distance = await run_in_threadpool(
            db.scalar, 
            query, 
            {"point": point_wkt, "line": linestring_wkt}
        )
        
        if distance is None:
            distance = 0.0

        is_deviated = distance > DEVIATION_THRESHOLD_METERS
        
        # Log breadcrumb history
        breadcrumb = json.dumps({"lat": current_lat, "lon": current_lon, "t": timestamp})
        
        async with redis_client.pipeline(transaction=True) as pipe:
            await pipe.rpush(history_key, breadcrumb)
            # 🔥 FIX (Bug 3.4): Trim the Redis list to keep only the last 50 pings!
            await pipe.ltrim(history_key, -50, -1)
            await pipe.expire(history_key, SESSION_TTL_SECONDS)
            await pipe.hset(session_id, "is_deviated", str(is_deviated))
            await pipe.execute()
            
        return is_deviated, float(distance)