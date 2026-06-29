import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.db.base_class import Base

class Incident(Base):
    """Module 1 [P0]: Crowdsourced safety updates weighted by trust."""
    __tablename__ = "incidents"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    category = Column(String, nullable=False)  # e.g., "harassment", "poor_lighting", "stalking"
    description = Column(String, nullable=True)
    audio_transcript = Column(String, nullable=True) # Gemini-transcribed notes
    
    # 🔥 FIX (Audit Fields): Track which NGO moderated this
    verified_by_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    flagged_by_id = Column(Integer, ForeignKey("user.id", ondelete="SET NULL"), nullable=True)
    
    # Spatial Point: Coordinates stored as (Longitude, Latitude)
    location = Column(Geometry(geometry_type="POINT", srid=4326, spatial_index=True), nullable=False)
    
    # Temporal decay inputs
    created_at = Column(DateTime, default=datetime.datetime.utcnow, index=True)
    is_active = Column(Boolean, default=True, index=True)
    
    # Structural relations
    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reported_incidents")
    verifier = relationship("User", foreign_keys=[verified_by_id])
    flagger = relationship("User", foreign_keys=[flagged_by_id])


class ColdStartPrior(Base):
    """Module 1 [P0]: Base safety telemetry compiled from OSM / municipal metadata."""
    __tablename__ = "cold_start_priors"

    id = Column(Integer, primary_key=True, index=True)
    city = Column(String, index=True, nullable=False)
    
    # Can represent a street segment line string or a specific feature point
    geom = Column(Geometry(geometry_type="GEOMETRY", srid=4326, spatial_index=True), nullable=False)
    
    # Static metric layers
    street_lighting_score = Column(Float, default=0.5)  # Derived from OSM tags
    commercial_density_score = Column(Float, default=0.5) # Shop/footfall proxies
    historical_crime_weight = Column(Float, default=0.0)  # Public open data
    
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)