from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "ACRA AI"
    environment: str = "development"
    database_url: str = "sqlite+aiosqlite:///./acra.db"
    github_api_base: str = "https://api.github.com"
    openrouter_api_base: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "qwen/qwen3-235b-a22b-thinking-2507"
    openrouter_api_key: str = ""
    request_timeout_s: int = 60
    max_file_bytes: int = 400_000
    chunk_char_limit: int = 8_000
    max_files: int = 2_000
    allow_git_clone_default: bool = False
    max_concurrent_chunks: int = 2
    api_key: str = ""
    cors_allow_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    rate_limit_per_minute: int = 60
    rate_limit_window_s: int = 60

    @field_validator("cors_allow_origins", mode="before")
    @classmethod
    def _parse_origins(cls, value):
        if isinstance(value, str):
            return [v.strip() for v in value.split(",") if v.strip()]
        return value

    model_config = SettingsConfigDict(env_file=[".env", "../.env"], env_prefix="ACRA_", extra="ignore")


settings = Settings()
