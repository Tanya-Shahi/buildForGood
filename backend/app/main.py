from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.session import init_spatial_db, engine
from app.db.base_class import Base

# 🔥 IMPORT ALL MODELS so create_all() sees them
from app.models.user import User
from app.models.route import Incident, ColdStartPrior
from app.models.support import ForumPost, ForumReply
from app.models.incident_log import IncidentLog 
from app.models.shelter import Shelter # 🔥 ADDED: The new Module 2 Shelter model!

# Imported the routers
from app.api.v1 import auth, routes, legal, telemetry, live_alerts, escalation, evidence_bridge, sensors, support 

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_spatial_db()
    Base.metadata.create_all(bind=engine)
    print("🚀 PostGIS active and database tables synced successfully.")

@app.get("/")
def root_check():
    return {"status": "healthy", "platform": "AWAAZ Women's Safety System", "year": 2026}

# Register the endpoints
app.include_router(auth.router, prefix="/api/v1/auth", tags=["Authentication"])
app.include_router(routes.router, prefix=settings.API_V1_STR + "/routes", tags=["Safe Routes"])
app.include_router(legal.router, prefix=settings.API_V1_STR + "/legal", tags=["Legal Companion"])
app.include_router(telemetry.router, prefix=settings.API_V1_STR + "/telemetry", tags=["Telemetry Monitoring"])
app.include_router(live_alerts.router, prefix=settings.API_V1_STR + "/alerts", tags=["Live Alerts"])
app.include_router(escalation.router, prefix=settings.API_V1_STR + "/escalation", tags=["Emergency Escalation"])
app.include_router(evidence_bridge.router, prefix="/api/v1/bridge", tags=["Evidence & ML"])
app.include_router(sensors.router, prefix="/api/v1/sensors", tags=["Device Sensors"])
app.include_router(support.router, prefix="/api/v1/support", tags=["Peer Support & Education"])