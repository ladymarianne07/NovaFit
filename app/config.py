import os
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration"""
    
    # App settings
    APP_NAME: str = "NovaFitness API"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    APP_TIMEZONE: str = "America/Argentina/Buenos_Aires"
    
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
        "https://nova-fit-kappa.vercel.app",  # Vercel production frontend
        "https://*.vercel.app",  # All Vercel preview deployments
        # Add your custom domain here when available
        # "https://novafitness.com",
    ]
    
    # Tunnel settings (for documentation)
    TUNNEL_URL: Optional[str] = None  # Set when using ngrok/cloudflare tunnel

    # External nutrition provider API keys
    USDA_API_KEY: Optional[str] = None
    OPENFOODFACTS_USER_AGENT: str = "NovaFitness/1.0 (contact: support@novafitness.local)"
    FATSECRET_CLIENT_ID: Optional[str] = None
    FATSECRET_CLIENT_SECRET: Optional[str] = None
    GEMINI_API_KEY: Optional[str] = None
    GEMINI_MODEL: str = "gemini-1.5-flash"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()