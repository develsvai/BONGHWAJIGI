from typing import Literal

from pydantic import Field, SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="BONGHWA_", env_file=".env", extra="ignore")

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

    @model_validator(mode="after")
    def check_token_budget(self) -> "Settings":
        if self.gpu_max_output_tokens >= self.gpu_max_total_tokens:
            raise ValueError("출력 토큰 상한은 전체 토큰 상한보다 작아야 합니다.")
        return self
