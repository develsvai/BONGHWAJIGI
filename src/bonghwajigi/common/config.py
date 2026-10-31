import os
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="BONGHWA_", env_file=os.environ.get("BONGHWA_ENV_FILE", ".env"), extra="ignore"
    )

    environment: Literal["local", "test", "staging", "production"] = "local"
    mode: Literal["live", "simulation"] = "simulation"
    database_url: SecretStr | None = None
    broker_url: SecretStr | None = None
    service_token: SecretStr | None = None
    gpu_base_url: str = "http://127.0.0.1:8001"
    qwen_model: str = "Qwen/Qwen3-4B-Instruct-2507"
    embedding_model: str = "Qwen/Qwen3-Embedding-0.6B"
    gpu_max_total_tokens: int = Field(default=4096, ge=1, le=4096)
    gpu_max_output_tokens: int = Field(default=512, ge=1, le=512)
    gpu_enabled: bool = False
    qwen_revision: str | None = None
    embedding_revision: str | None = None
    gpu_lock_path: Path = Path.home() / ".cache/bonghwajigi/gpu.lock"
    analysis_enabled: bool = False
    embedding_service_token: SecretStr | None = None
    embedding_timeout_seconds: float = Field(default=30, ge=1, le=120)
    retrieval_top_k: int = Field(default=5, ge=1, le=10)
    web_search_enabled: bool = True
    web_search_max_results: int = Field(default=5, ge=1, le=10)
    web_search_lookback_days: int = Field(default=7, ge=1, le=365)
    outbox_redelivery_seconds: int = Field(default=180, ge=10, le=3600)
    policy_enabled: bool = False
    policy_qwen_enabled: bool = False
    policy_poll_seconds: float = Field(default=2, ge=0.2, le=60)
    policy_check_seconds: int = Field(default=30, ge=1, le=3600)
    notifications_enabled: bool = False
    push_provider: Literal["disabled", "simulation", "fcm"] = "disabled"
    fcm_project_id: str | None = None
    fcm_credentials_file: Path | None = None
    app_enabled: bool = False
    jwt_secret: SecretStr | None = None
    jwt_issuer: str = "bonghwajigi-mvp"
    jwt_audience: str = "bonghwajigi-app"
    jwt_lifetime_seconds: int = Field(default=86400, ge=300, le=604800)

    @model_validator(mode="after")
    def check_token_budget(self) -> "Settings":
        if self.gpu_max_output_tokens >= self.gpu_max_total_tokens:
            raise ValueError("출력 토큰 상한은 전체 토큰 상한보다 작아야 합니다.")
        return self
