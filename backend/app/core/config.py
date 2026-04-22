from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Resume Optimizer Agent"
    app_env: str = "development"
    api_prefix: str = "/api"
    debug: bool = True

    deepseek_api_key: str | None = Field(default=None, alias="DEEPSEEK_API_KEY")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1", alias="DEEPSEEK_BASE_URL"
    )
    deepseek_model: str = Field(default="deepseek-chat", alias="DEEPSEEK_MODEL")
    deepseek_timeout_seconds: float = Field(default=90.0, alias="DEEPSEEK_TIMEOUT_SECONDS")
    deepseek_max_retries: int = Field(default=2, alias="DEEPSEEK_MAX_RETRIES")

    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://localhost:3000"]
    )
    max_upload_size_mb: int = 10
    allowed_extensions: List[str] = Field(
        default_factory=lambda: [".pdf", ".docx", ".md", ".txt"]
    )
    export_dir: str = "/tmp/resume-optimizer-exports"
    backend_port: int = 8000
    frontend_port: int = 8080

    model_config = SettingsConfigDict(
        env_prefix="RESUME_OPTIMIZER_",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()
