from pydantic import BaseSettings, Field
from typing import Optional, Dict, List, Any


class LLMSettings(BaseSettings):
    api_key: str = Field(..., env="OPENROUTER_API_KEY")
    base_url: str = Field("https://openrouter.ai/api/v1", env="LLM_BASE_URL")
    default_model: str = Field("anthropic/claude-3-opus-20240229", env="DEFAULT_MODEL")
    timeout: int = Field(60, env="LLM_TIMEOUT")
    max_tokens: int = Field(4000, env="LLM_MAX_TOKENS")
    temperature: float = Field(0.7, env="LLM_TEMPERATURE")


class ChromaSettings(BaseSettings):
    host: str = Field("chroma", env="CHROMA_HOST")
    port: int = Field(8000, env="CHROMA_PORT")
    collection_name: str = Field("m31_memory", env="CHROMA_COLLECTION")


class RedisSettings(BaseSettings):
    host: str = Field("redis", env="REDIS_HOST")
    port: int = Field(6379, env="REDIS_PORT")
    db: int = Field(0, env="REDIS_DB")
    password: Optional[str] = Field(None, env="REDIS_PASSWORD")
    ttl: int = Field(3600, env="REDIS_TTL")


class CelerySettings(BaseSettings):
    broker_url: str = Field("redis://redis:6379/0", env="CELERY_BROKER")
    result_backend: str = Field("redis://redis:6379/0", env="CELERY_BACKEND")
    task_serializer: str = Field("json", env="CELERY_TASK_SERIALIZER")
    result_serializer: str = Field("json", env="CELERY_RESULT_SERIALIZER")


class APISettings(BaseSettings):
    host: str = Field("0.0.0.0", env="API_HOST")
    port: int = Field(8000, env="API_PORT")
    debug: bool = Field(False, env="API_DEBUG")
    cors_origins: List[str] = Field(["http://localhost:3000"], env="CORS_ORIGINS")


class Settings(BaseSettings):
    app_name: str = Field("M31-Mini", env="APP_NAME")
    log_level: str = Field("INFO", env="LOG_LEVEL")
    llm: LLMSettings = LLMSettings()
    chroma: ChromaSettings = ChromaSettings()
    redis: RedisSettings = RedisSettings()
    celery: CelerySettings = CelerySettings()
    api: APISettings = APISettings()
    allowed_shell_commands: List[str] = Field(
        ["ls", "cat", "head", "tail", "grep", "find"], env="ALLOWED_COMMANDS"
    )
    tools_enabled: List[str] = Field(
        ["web_search", "file_io", "shell"], env="TOOLS_ENABLED"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings() 