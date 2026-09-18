"""Application configuration loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Backend settings, loaded from .env or environment."""

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    debug: bool = True

    # LLM Provider — switch between "mock" and "gemini" via env/config
    llm_provider: str = "mock"
    llm_api_key: str = ""  # GOOGLE_API_KEY — never commit real keys
    llm_model: str = "gemini-2.0-flash"
    llm_timeout: int = 30
    llm_max_retries: int = 3
    llm_base_url: str = "https://generativelanguage.googleapis.com/v1beta"

    # Exploration
    max_step_budget: int = 50
    session_timeout_seconds: int = 600

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
