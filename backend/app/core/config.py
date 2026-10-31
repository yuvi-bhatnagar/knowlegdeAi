import json
from pathlib import Path
from typing import Any, Literal
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


ProviderType = Literal["openai", "gemini", "ollama"]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # Application settings
    APP_NAME: str = "KnowledgeAI"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "insecure-dev-secret-key-change-in-production-min32bytes!"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://knowledge_user:knowledge_pass@localhost:5432/knowledge_ai"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20

    # Redis & Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Qdrant Vector DB
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION_PREFIX: str = "knowledge_ai"

    # Storage
    STORAGE_DIR: str = "./storage"
    MAX_UPLOAD_SIZE_BYTES: int = 26_214_400  # 25 MB

    # AI Provider Selection
    AI_CHAT_PROVIDER: ProviderType = "openai"
    AI_EMBEDDING_PROVIDER: ProviderType = "openai"

    # OpenAI Configuration
    OPENAI_API_KEY: str | None = None
    OPENAI_CHAT_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # Google Gemini Configuration
    GEMINI_API_KEY: str | None = None
    GEMINI_CHAT_MODEL: str = "gemini-2.5-flash-lite"
    GEMINI_EMBEDDING_MODEL: str = "gemini-embedding-001"

    # Ollama (Local) Configuration
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_CHAT_MODEL: str = "llama3.2"
    OLLAMA_EMBEDDING_MODEL: str = "nomic-embed-text"

    # AI Execution Parameters
    AI_REQUEST_TIMEOUT_SECONDS: float = 60.0
    AI_MAX_RETRIES: int = 2
    AI_TEMPERATURE: float = 0.2
    AI_MAX_OUTPUT_TOKENS: int = 2048

    # RAG & Chunking
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150
    RAG_TOP_K: int = 5
    RAG_SIMILARITY_THRESHOLD: float = 0.50

    # CORS
    CORS_ORIGINS: list[str] = [
        "http://localhost:5173",
        "http://localhost:3000",
        "http://127.0.0.1:5173",
    ]

    # Email Provider Selection (mailinator | sendgrid | smtp | console)
    EMAIL_PROVIDER: str = "mailinator"

    # Mailinator Configuration
    MAILINATOR_API_KEY: str | None = None
    MAILINATOR_DOMAIN: str = "mailinator.com"

    # SendGrid Configuration
    SENDGRID_API_KEY: str | None = None
    SENDGRID_FROM_EMAIL: str = "noreply@knowledgeai.com"

    # Email & SMTP Configuration (Supports Mailinator, SendGrid & Standard SMTP)
    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_TLS: bool = True
    EMAILS_FROM_EMAIL: str = "noreply@knowledgeai.local"
    FRONTEND_URL: str = "http://localhost:5173"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> list[str]:
        if isinstance(v, str):
            if v.startswith("[") and v.endswith("]"):
                try:
                    return json.loads(v)
                except Exception:
                    pass
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, list):
            return [str(item) for item in v]
        return ["*"]

    @property
    def storage_path(self) -> Path:
        path = Path(self.STORAGE_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path

    def validate_provider_configuration(self) -> dict[str, Any]:
        """Validate that the configured chat and embedding providers have required credentials."""
        diagnostics = {
            "chat_provider": self.AI_CHAT_PROVIDER,
            "embedding_provider": self.AI_EMBEDDING_PROVIDER,
            "chat_ready": False,
            "embedding_ready": False,
            "errors": [],
        }

        # Check Chat Provider
        if self.AI_CHAT_PROVIDER == "openai":
            if not self.OPENAI_API_KEY or not self.OPENAI_API_KEY.strip():
                diagnostics["errors"].append("OPENAI_API_KEY is required for OpenAI chat provider.")
            else:
                diagnostics["chat_ready"] = True
        elif self.AI_CHAT_PROVIDER == "gemini":
            if not self.GEMINI_API_KEY or not self.GEMINI_API_KEY.strip():
                diagnostics["errors"].append("GEMINI_API_KEY is required for Gemini chat provider.")
            else:
                diagnostics["chat_ready"] = True
        elif self.AI_CHAT_PROVIDER == "ollama":
            diagnostics["chat_ready"] = True

        # Check Embedding Provider
        if self.AI_EMBEDDING_PROVIDER == "openai":
            if not self.OPENAI_API_KEY or not self.OPENAI_API_KEY.strip():
                diagnostics["errors"].append("OPENAI_API_KEY is required for OpenAI embedding provider.")
            else:
                diagnostics["embedding_ready"] = True
        elif self.AI_EMBEDDING_PROVIDER == "gemini":
            if not self.GEMINI_API_KEY or not self.GEMINI_API_KEY.strip():
                diagnostics["errors"].append("GEMINI_API_KEY is required for Gemini embedding provider.")
            else:
                diagnostics["embedding_ready"] = True
        elif self.AI_EMBEDDING_PROVIDER == "ollama":
            diagnostics["embedding_ready"] = True

        # Check Email Provider
        diagnostics["email_provider"] = self.EMAIL_PROVIDER
        diagnostics["email_ready"] = False
        email_prov = self.EMAIL_PROVIDER.lower()
        if email_prov in ("mailinator", "console"):
            diagnostics["email_ready"] = True
        elif email_prov == "sendgrid":
            if not self.SENDGRID_API_KEY or not self.SENDGRID_API_KEY.strip():
                diagnostics["errors"].append("SENDGRID_API_KEY is required when EMAIL_PROVIDER=sendgrid.")
            else:
                diagnostics["email_ready"] = True
        elif email_prov == "smtp":
            if not self.SMTP_HOST or not self.SMTP_HOST.strip():
                diagnostics["errors"].append("SMTP_HOST is required when EMAIL_PROVIDER=smtp.")
            else:
                diagnostics["email_ready"] = True
        else:
            diagnostics["errors"].append(f"Unsupported EMAIL_PROVIDER '{self.EMAIL_PROVIDER}'. Choose from mailinator, sendgrid, smtp, console.")

        return diagnostics


settings = Settings()
