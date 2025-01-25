"""
Configuration management using environment variables.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file only if not in test mode
if "PYTEST_CURRENT_TEST" not in os.environ:
    load_dotenv()


class Config:
    """Application configuration from environment variables."""

    # OpenAI Configuration
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")

    # PodcastIndex API Configuration
    PODCASTINDEX_API_KEY: str = os.getenv("PODCASTINDEX_API_KEY", "")
    PODCASTINDEX_API_SECRET: str = os.getenv("PODCASTINDEX_API_SECRET", "")

    # Ngrok Configuration
    NGROK_AUTH_TOKEN: str = os.getenv("NGROK_AUTH_TOKEN", "")
    NGROK_URL: str = os.getenv(
        "NGROK_URL", "https://2f21-134-195-195-182.ngrok-free.app"
    )
    TRANSCRIPTION_SERVER_TOKEN: str = os.getenv(
        "TRANSCRIPTION_SERVER_TOKEN", "chamberOfSecrets"
    )

    # YouTube API Configuration
    YOUTUBE_API_KEY: str = os.getenv("YOUTUBE_API_KEY", "")

    # Redis Configuration
    REDIS_HOST: str = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT: int = int(os.getenv("REDIS_PORT", "6379"))
    REDIS_DB: int = int(os.getenv("REDIS_DB", "0"))
    REDIS_PASSWORD: str = os.getenv("REDIS_PASSWORD", "")

    # Application Settings
    APP_ENV: str = os.getenv("APP_ENV", "development")
    DEBUG: bool = os.getenv("DEBUG", "true").lower() == "true"
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # Feature Flags
    USE_OPENAI_WHISPER: bool = os.getenv("USE_OPENAI_WHISPER", "true").lower() == "true"
    USE_REMOTE_WHISPER: bool = (
        os.getenv("USE_REMOTE_WHISPER", "false").lower() == "true"
    )
    PREFER_YOUTUBE_TRANSCRIPTS: bool = (
        os.getenv("PREFER_YOUTUBE_TRANSCRIPTS", "true").lower() == "true"
    )
    CACHE_TRANSCRIPTS: bool = os.getenv("CACHE_TRANSCRIPTS", "true").lower() == "true"

    # Cache Settings
    CACHE_DIR: Path = Path(os.getenv("CACHE_DIR", "./transcript_cache"))
    MAX_CACHE_SIZE_MB: int = int(os.getenv("MAX_CACHE_SIZE_MB", "500"))

    # Rate Limiting
    DEMO_USER_LIMIT: int = int(os.getenv("DEMO_USER_LIMIT", "2"))
    RATE_LIMIT_WINDOW: int = int(os.getenv("RATE_LIMIT_WINDOW", "86400"))

    # Security
    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-secret-key-change-in-production")
    JWT_SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY", "default-jwt-secret-change-in-production"
    )

    # Streamlit Configuration
    STREAMLIT_SERVER_PORT: int = int(os.getenv("STREAMLIT_SERVER_PORT", "8501"))
    STREAMLIT_SERVER_ADDRESS: str = os.getenv("STREAMLIT_SERVER_ADDRESS", "localhost")

    # Google Cloud Configuration
    GCP_PROJECT_ID: str = os.getenv("GCP_PROJECT_ID", "")
    GCP_REGION: str = os.getenv("GCP_REGION", "us-central1")
    CLOUD_RUN_SERVICE_NAME: str = os.getenv("CLOUD_RUN_SERVICE_NAME", "ekko-app")

    # CrewAI Configuration
    CREWAI_API_KEY: str = os.getenv("CREWAI_API_KEY", "")
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")

    @classmethod
    def validate(cls) -> bool:
        """Validate required configuration values."""
        errors = []

        # Check required API keys for core functionality
        if not cls.OPENAI_API_KEY:
            errors.append("OPENAI_API_KEY is not set")

        if not cls.PODCASTINDEX_API_KEY or not cls.PODCASTINDEX_API_SECRET:
            errors.append("PodcastIndex API credentials are not set")

        if errors:
            for error in errors:
                print(f"Configuration Error: {error}")
            return False

        return True

    @classmethod
    def get_openai_config(cls) -> dict:
        """Get OpenAI configuration dictionary."""
        return {"api_key": cls.OPENAI_API_KEY}

    @classmethod
    def get_podcastindex_config(cls) -> dict:
        """Get PodcastIndex configuration dictionary."""
        return {
            "api_key": cls.PODCASTINDEX_API_KEY,
            "api_secret": cls.PODCASTINDEX_API_SECRET,
        }

    @classmethod
    def get_ngrok_config(cls) -> dict:
        """Get Ngrok configuration dictionary."""
        return {
            "auth_token": cls.NGROK_AUTH_TOKEN,
            "url": cls.NGROK_URL,
            "server_token": cls.TRANSCRIPTION_SERVER_TOKEN,
        }

    @classmethod
    def get_redis_url(cls) -> str:
        """Get Redis connection URL."""
        if cls.REDIS_PASSWORD:
            return f"redis://:{cls.REDIS_PASSWORD}@{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"
        return f"redis://{cls.REDIS_HOST}:{cls.REDIS_PORT}/{cls.REDIS_DB}"


# Create a singleton config instance
config = Config()
