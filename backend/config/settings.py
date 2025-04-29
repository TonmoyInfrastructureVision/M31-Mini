from typing import Dict, List, Optional, Union
from pathlib import Path
import os

from pydantic import BaseModel, field_validator
from pydantic_settings import BaseSettings
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent


class APISettings(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = False
    cors_origins: List[str] = ["*"]
    
    @field_validator("cors_origins")
    def validate_cors_origins(cls, v, values):
        if v == ["*"]:
            return v
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v


class DatabaseSettings(BaseModel):
    url: str = "sqlite:///./m31mini.db"
    connect_args: Dict = {"check_same_thread": False}
    echo: bool = False


class SecuritySettings(BaseModel):
    secret_key: str = os.getenv("SECRET_KEY", "secret_key_for_development_only")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30


class ChromaSettings(BaseModel):
    host: Optional[str] = "localhost"
    port: Optional[int] = 8000
    persist_directory: str = str(BASE_DIR / "data" / "chroma")
    embedding_model: str = "all-MiniLM-L6-v2"


class RedisSettings(BaseModel):
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    use_ssl: bool = False


class CelerySettings(BaseModel):
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/0"
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: List[str] = ["json"]
    enable_utc: bool = True


class LLMSettings(BaseModel):
    provider: str = "openai"
    model: str = "gpt-4"
    api_key: str = os.getenv("OPENAI_API_KEY", "")
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    temperature: float = 0.7
    timeout: int = 60


class AgentSettings(BaseModel):
    workspace_root: str = str(BASE_DIR / "workspaces")
    default_model: str = "gpt-4"
    max_planning_steps: int = 15
    max_execution_steps: int = 50


class Settings(BaseSettings):
    api: APISettings = APISettings()
    db: DatabaseSettings = DatabaseSettings()
    security: SecuritySettings = SecuritySettings()
    chroma: ChromaSettings = ChromaSettings()
    redis: RedisSettings = RedisSettings()
    celery: CelerySettings = CelerySettings()
    llm: LLMSettings = LLMSettings()
    agent: AgentSettings = AgentSettings()
    log_level: str = "INFO"
    environment: str = os.getenv("ENVIRONMENT", "development")


# Create settings instance
settings = Settings()

# Environment-specific overrides
if settings.environment == "production":
    settings.api.debug = False
    settings.api.cors_origins = os.getenv("CORS_ORIGINS", "").split(",")
    settings.db.echo = False
    settings.security.secret_key = os.getenv("SECRET_KEY")
    if not settings.security.secret_key:
        raise ValueError("SECRET_KEY environment variable is required in production mode")
    
    # Redis connection in production may use SSL
    redis_url = os.getenv("REDIS_URL")
    if redis_url and redis_url.startswith("rediss://"):
        settings.redis.use_ssl = True 