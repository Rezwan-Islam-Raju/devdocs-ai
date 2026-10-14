from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # Application Config
    APP_NAME: str = "DevDocs AI"
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

    # ☁ Supabase Storage Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_BUCKET_NAME: str = "devdocs-documents"

    #  AI / LLM Configuration
    LLM_PROVIDER: str = "ollama"
    OLLAMA_BASE_URL: str = "http://127.0.0.1:11434"
    OLLAMA_MODEL: str = "qwen3:4b"
    GEMINI_API_KEY: str = "optional_gemini_key"


    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        env_file_override=True,
        extra="ignore"
    )


settings = Settings()


