"""
Configuration settings for the ADRIE application, loaded from environment variables.
Uses Pydantic's BaseSettings for easy validation and management.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    """
    model_config = SettingsConfigDict(env_file='.env', extra='ignore')

    APP_NAME: str = "ADRIE"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development" # e.g., 'development', 'staging', 'production'

    # LLM Settings for Explainability Module
    LLM_PROVIDER: str = "mock" # e.g., 'mock', 'google_gemini', 'openai'
    GOOGLE_GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Database Settings (if any, for persistence)
    DATABASE_URL: Optional[str] = None # e.g., "sqlite:///./adrie.db"

    # Simulation Defaults
    DEFAULT_MAP_SIZE: int = 50
    DEFAULT_HAZARD_INTENSITY_FACTOR: float = 0.5
    DEFAULT_NUM_VICTIMS: int = 10
    DEFAULT_NUM_AGENTS: int = 3

    # Logging Settings
    LOG_LEVEL: str = "INFO" # e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    LOG_FILE_PATH: Optional[str] = "logs/adrie.log"

    class Config:
        """Pydantic config for Settings."""
        env_file = ".env"
        env_file_encoding = "utf-8"

# Instantiate settings to be imported across the application
settings = Settings()
