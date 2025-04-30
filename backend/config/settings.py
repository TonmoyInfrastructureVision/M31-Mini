from typing import Dict, Any, List, Optional, Union, Set
from pathlib import Path
import os
import json

from pydantic import BaseModel, field_validator, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
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
    prefix: str = "/api/v1"
    workers: int = 4
    timeout_seconds: int = 300
    ssl_keyfile: Optional[str] = None
    ssl_certfile: Optional[str] = None
    log_level: str = "info"
    rate_limit_per_minute: int = 100
    
    @field_validator("cors_origins")
    def validate_cors_origins(cls, v, values):
        if v == ["*"]:
            return v
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v


class DatabaseSettings(BaseModel):
    url: str = "sqlite:///./m31_mini.db"
    connect_args: Dict[str, Any] = {"check_same_thread": False}
    echo: bool = False
    pool_size: int = 20
    max_overflow: int = 20
    pool_timeout: int = 30
    run_migrations: bool = True
    backup_dir: str = "./backups"
    auto_backup: bool = True
    backup_frequency_hours: int = 24


class SecuritySettings(BaseModel):
    secret_key: str = "CHANGE_ME_IN_PRODUCTION"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    password_min_length: int = 8
    password_max_length: int = 64
    enable_rate_limiting: bool = True
    rate_limit_per_minute: int = 60
    jwt_token_prefix: str = "Bearer"
    allowed_hosts: List[str] = ["*"]
    api_key_enabled: bool = True
    api_key_header_name: str = "X-API-Key"
    strict_transport_security: bool = False


class ChromaSettings(BaseModel):
    host: Optional[str] = "localhost"
    port: Optional[int] = 8000
    persist_directory: str = str(BASE_DIR / "data" / "chroma")
    embedding_model: str = "all-MiniLM-L6-v2"


class RedisSettings(BaseModel):
    host: str = "localhost"
    port: int = 6379
    password: Optional[str] = None
    db: int = 0
    ssl: bool = False
    socket_timeout: int = 5
    socket_connect_timeout: int = 5
    connection_pool_size: int = 10
    use_sentinel: bool = False
    sentinel_master: Optional[str] = None
    sentinel_hosts: List[str] = []


class CelerySettings(BaseModel):
    broker_url: str = "redis://localhost:6379/0"
    result_backend: str = "redis://localhost:6379/0"
    task_serializer: str = "json"
    result_serializer: str = "json"
    accept_content: List[str] = ["json"]
    enable_utc: bool = True


class LLMProviderSettings(BaseModel):
    provider: str = "openai"
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None
    azure_api_key: Optional[str] = None
    azure_endpoint: Optional[str] = None
    azure_deployment_id: Optional[str] = None
    ollama_base_url: Optional[str] = None
    local_model_path: Optional[str] = None
    huggingface_api_key: Optional[str] = None
    together_api_key: Optional[str] = None


class AgentSettings(BaseModel):
    workspace_root: str = "./workspaces"
    default_model: str = "gpt-4o"
    structured_output_model: str = "gpt-4o"
    max_iterations: int = 10
    default_temperature: float = 0.7
    max_tokens: int = 4000
    max_history_tokens: int = 16000
    max_concurrent_agents: int = 5
    tool_execution_timeout: int = 60
    plan_iterations: int = 3
    execution_memory_limit: int = 1000
    reflection_enabled: bool = True


class MemorySettings(BaseModel):
    vector_db_type: str = "chroma"
    chroma_persist_directory: str = "./chromadb" 
    embedding_model: str = "all-MiniLM-L6-v2"
    redis_ttl_seconds: int = 3600
    max_short_term_history: int = 100
    similarity_score_threshold: float = 0.7
    chunk_size: int = 1000
    chunk_overlap: int = 200
    caching_enabled: bool = True
    cache_ttl_seconds: int = 3600
    structured_storage_enabled: bool = True


class LoggingSettings(BaseModel):
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file: Optional[str] = "./logs/m31_mini.log"
    max_size_mb: int = 10
    backup_count: int = 5
    json_logs: bool = False
    logstash_enabled: bool = False
    logstash_host: Optional[str] = None
    logstash_port: Optional[int] = None


class SchedulerSettings(BaseModel):
    broker_url: str = "redis://localhost:6379/1"
    result_backend: str = "redis://localhost:6379/1"
    task_serializer: str = "json"
    accept_content: List[str] = ["json"]
    result_serializer: str = "json"
    enable_utc: bool = True
    worker_concurrency: int = 4
    task_time_limit: int = 3600
    task_soft_time_limit: int = 3000
    worker_prefetch_multiplier: int = 1
    beat_enabled: bool = True
    periodic_task_scan_interval: int = 30
    max_retries: int = 3
    retry_delay: int = 300


class ToolSettings(BaseModel):
    web_search_enabled: bool = True
    web_search_provider: str = "duckduckgo"
    google_search_api_key: Optional[str] = None
    google_search_engine_id: Optional[str] = None
    shell_command_enabled: bool = False
    shell_command_timeout: int = 30
    shell_command_allowlist: List[str] = []
    file_io_enabled: bool = True
    max_file_size_mb: int = 50
    allowed_file_extensions: Set[str] = {"txt", "md", "csv", "json", "py", "js", "html", "css"}
    file_operations_root: Optional[str] = None


class Settings(BaseSettings):
    project_name: str = "M31-Mini Agent Framework"
    version: str = "0.2.0"
    description: str = "A modular autonomous agent framework for real-world use cases"
    debug: bool = False
    environment: str = "development"

    db: DatabaseSettings = DatabaseSettings()
    api: APISettings = APISettings()
    agent: AgentSettings = AgentSettings()
    llm: LLMProviderSettings = LLMProviderSettings()
    redis: RedisSettings = RedisSettings()
    memory: MemorySettings = MemorySettings()
    logging: LoggingSettings = LoggingSettings()
    scheduler: SchedulerSettings = SchedulerSettings()  
    security: SecuritySettings = SecuritySettings()
    tools: ToolSettings = ToolSettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_nested_delimiter="__",
        extra="ignore"
    )

    @field_validator("environment")
    def validate_environment(cls, v: str) -> str:
        allowed_environments = ["development", "testing", "staging", "production"]
        if v not in allowed_environments:
            raise ValueError(f"Environment must be one of {allowed_environments}")
        return v

    def get_settings_dict(self) -> Dict[str, Any]:
        return {
            "project_name": self.project_name,
            "version": self.version,
            "description": self.description,
            "debug": self.debug,
            "environment": self.environment,
            "db": self.db.model_dump(exclude_none=True),
            "api": self.api.model_dump(exclude_none=True),
            "agent": self.agent.model_dump(exclude_none=True),
            "llm": self.llm.model_dump(exclude_unset=True, exclude={"openai_api_key", "anthropic_api_key", "azure_api_key", "huggingface_api_key", "together_api_key"}),
            "redis": self.redis.model_dump(exclude_none=True, exclude={"password"}),
            "memory": self.memory.model_dump(exclude_none=True),
            "logging": self.logging.model_dump(exclude_none=True),
            "scheduler": self.scheduler.model_dump(exclude_none=True),
            "security": self.security.model_dump(exclude={"secret_key"}),
            "tools": self.tools.model_dump(exclude_none=True),
        }

    def get_settings_json(self) -> str:
        return json.dumps(self.get_settings_dict(), indent=2)


# Create settings instance from environment variables and defaults
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
        settings.redis.ssl = True 