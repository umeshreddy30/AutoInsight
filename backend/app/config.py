"""
Application Configuration
Manages all environment variables and settings
"""
from pydantic_settings import BaseSettings
from pathlib import Path
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # API Configuration
    API_TITLE: str = "AutoInsight API"
    API_VERSION: str = "1.0.0"
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    DEBUG: bool = False
    
    # CORS Settings
    CORS_ORIGINS: list = ["http://localhost:3000", "http://localhost:5173"]
    
    # AI Provider Configuration
    AI_PROVIDER: str = "anthropic"  # "anthropic" or "openai"
    ANTHROPIC_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    
    # File Upload Settings
    MAX_FILE_SIZE: int = 100 * 1024 * 1024  # 100MB
    ALLOWED_EXTENSIONS: set = {".csv", ".xlsx", ".xls"}
    UPLOAD_DIR: Path = Path("uploads")
    REPORT_DIR: Path = Path("reports")
    LOG_DIR: Path = Path("logs")
    
    # Analysis Settings
    MAX_ROWS_PREVIEW: int = 10000
    CORRELATION_THRESHOLD: float = 0.7
    OUTLIER_STD_THRESHOLD: float = 3.0
    
    # Database Configuration
    DATABASE_URL: str = "sqlite+aiosqlite:///./autoinsight.db"
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# Create settings instance
settings = Settings()

# Ensure required directories exist
settings.UPLOAD_DIR.mkdir(exist_ok=True)
settings.REPORT_DIR.mkdir(exist_ok=True)
settings.LOG_DIR.mkdir(exist_ok=True)