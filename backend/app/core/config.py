# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import ConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "AWAAZ - Women's Safety Lifecycle Platform"
    API_V1_STR: str = "/api/v1"
    
    # Infrastructure URLs
    DATABASE_URL: str = "postgresql://awaaz_dev:password_change_me_2026@localhost:5433/awaaz_spatial_db"
    REDIS_URL: str = "redis://localhost:6380/0"
    
    # AI Core
    GEMINI_API_KEY: str
    
    # Security
    SECRET_KEY: str = "SUPER_SECRET_COMPROMISED_HACKATHON_KEY_2026"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 1 week

    model_config = ConfigDict(case_sensitive=True, env_file=".env")

settings = Settings()