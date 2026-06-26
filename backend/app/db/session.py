# app/db/session.py
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL, 
    pool_pre_ping=True,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_spatial_db():
    """Ensure the PostGIS extension is loaded before creating tables."""
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()

def get_db():
    """FastAPI Dependency for context-managed database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()