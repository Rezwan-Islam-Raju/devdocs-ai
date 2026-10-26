from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Application Config
    APP_NAME: str = "Rezifa AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Database Config
    DATABASE_URL: str

    # Authentication Config
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    # Token Expiration Config
    ACCESS_TOKEN_EXPIRE_HOURS: int = 8
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # Supabase Storage Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_BUCKET_NAME: str = "devdocs-documents"

    # Default LLM Provider
    LLM_PROVIDER: str = "gemini"

    # Ollama Configuration
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen3:4b"

    # Google Gemini Configuration
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-3.5-flash-lite"
    GEMINI_FREE_MODELS: str = ""

    # OpenRouter Configuration
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Model Selection
    DEFAULT_MODEL_PROVIDER: str = "gemini"
    DEFAULT_MODEL: str = "gemini-3.5-flash-lite"

    # Automatic Fallback
    ENABLE_MODEL_FALLBACK: bool = False

    # Retry Configuration
    LLM_MAX_RETRIES: int = 2
    LLM_TIMEOUT_SECONDS: int = 90

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
