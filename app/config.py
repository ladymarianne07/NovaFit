import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration"""
    
    # App settings
    APP_NAME: str = "NovaFitness API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    
    # Database
    DATABASE_URL: str = "sqlite:///./novafitness.db"
    # For PostgreSQL migration, change to:
    # DATABASE_URL: str = "postgresql://user:password@localhost/novafitness"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 525600  # 1 year (365 days) - session lasts until user logs out
    
    # CORS settings for PWA
    ALLOWED_ORIGINS: list[str] = [
        "http://localhost:3000",  # Development frontend
        "https://localhost:3000", 
        "https://novafitness-frontend.onrender.com",  # Production frontend
        "https://*.onrender.com",  # Render.com domains
        # Add your custom domain here when available
        # "https://novafitness.com",
    ]
    
    # Tunnel settings (for documentation)
    TUNNEL_URL: Optional[str] = None  # Set when using ngrok/cloudflare tunnel
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()