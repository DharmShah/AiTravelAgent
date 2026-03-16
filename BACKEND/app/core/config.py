from functools import cached_property

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Travel Agent API"
    app_version: str = "1.0.0"
    openrouter_api_key: str | None = None
    openrouter_model: str = "openai/gpt-4.1-mini"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_site_url: str = "http://localhost:5176"
    openrouter_app_name: str = "AI Travel Agent"
    frontend_origins: str = "http://localhost:5176,http://127.0.0.1:5176"
    flight_data_mode: str = "hybrid"
    request_timeout_seconds: int = 20

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @cached_property
    def allowed_origins(self) -> list[str]:
        return [origin.strip() for origin in self.frontend_origins.split(",") if origin.strip()]


settings = Settings()