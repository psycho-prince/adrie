"""Configuration settings for the ADRIE application.

Loaded from environment variables, uses Pydantic's BaseSettings for easy validation and management.
"""

from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )

    APP_NAME: str = "ADRIE"
    APP_VERSION: str = "0.1.0"
    ENVIRONMENT: str = "development"  # e.g., 'development', 'staging', 'production'

    # LLM Settings for Explainability Module
    LLM_PROVIDER: str = "mock"  # e.g., 'mock', 'google_gemini', 'openai'
    GOOGLE_GEMINI_API_KEY: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None

    # Database Settings (if any, for persistence)
    DATABASE_URL: Optional[str] = None  # e.g., "sqlite:///./adrie.db"

    # Simulation Defaults
    DEFAULT_MAP_SIZE: int = 50
    DEFAULT_HAZARD_INTENSITY_FACTOR: float = 0.5
    DEFAULT_NUM_VICTIMS: int = 10
    DEFAULT_NUM_AGENTS: int = 3

    # Logging Settings
    LOG_LEVEL: str = "INFO"  # e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'
    LOG_FILE_PATH: Optional[str] = "logs/adrie.log"

    # Concurrency Settings
    MAX_WORKERS: int = 4  # Max workers for ThreadPoolExecutor for CPU-bound tasks

    # Risk Modeling Settings
    HAZARD_FIRE_WEIGHT: float = 0.8
    HAZARD_COLLAPSE_WEIGHT: float = 1.0
    HAZARD_FLOOD_WEIGHT: float = 0.6
    HAZARD_GAS_LEAK_WEIGHT: float = 0.9
    HAZARD_DEBRIS_WEIGHT: float = 0.4
    RISK_PROPAGATION_FACTOR: float = 0.1
    RISK_DECAY_FACTOR_BASE: float = 1.0  # This was 1.0 / distance, so base is 1.0

    # Prioritization Settings
    PRIORITIZATION_SEVERITY_WEIGHT: float = 0.4
    PRIORITIZATION_TIME_SENSITIVITY_WEIGHT: float = 0.3
    PRIORITIZATION_ACCESSIBILITY_RISK_WEIGHT: float = 0.2
    PRIORITIZATION_NUM_AGENTS_AVAILABLE_WEIGHT: float = 0.1
    PRIORITIZATION_SEVERITY_CRITICAL_SCORE: float = 1.0
    PRIORITIZATION_SEVERITY_SEVERE_SCORE: float = 0.75
    PRIORITIZATION_SEVERITY_MODERATE_SCORE: float = 0.5
    PRIORITIZATION_SEVERITY_MILD_SCORE: float = 0.25

    # Rate Limiting Settings
    RATE_LIMIT_REQUESTS_PER_INTERVAL: int = 100
    RATE_LIMIT_INTERVAL_SECONDS: int = 60


# Instantiate settings to be imported across the application
settings = Settings()
