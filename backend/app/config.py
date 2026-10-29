import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_ROOT = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_ROOT / ".env"), str(BACKEND_ROOT.parent / ".env")),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "EventWise AI — Smart Event Planning Assistant"
    APP_VERSION: str = "1.0.0"

    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2:3b"
    OLLAMA_TIMEOUT_SECONDS: float = 45.0

    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"
    CHROMA_PERSIST_DIRECTORY: str = str(BACKEND_ROOT / "chroma_db")
    CHROMA_COLLECTION_NAME: str = "eventwise_knowledge"

    SQLITE_DATABASE_URL: str = f"sqlite:///{(BACKEND_ROOT / 'eventwise.db').as_posix()}"

    MAX_UPLOAD_SIZE_MB: int = 10
    RAG_TOP_K: int = 5
    RAG_CHUNK_SIZE: int = 700
    RAG_CHUNK_OVERLAP: int = 100

    FRONTEND_ORIGIN: str = "http://localhost:3000"

    UPLOAD_DIRECTORY: str = str(BACKEND_ROOT / "data" / "documents")
    SAMPLE_DATA_DIRECTORY: str = str(BACKEND_ROOT / "data" / "sample_data")
    SEED_SAMPLE_DATA_ON_STARTUP: bool = True

    @property
    def max_upload_bytes(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    @property
    def allowed_origins(self) -> list[str]:
        origins = [o.strip() for o in self.FRONTEND_ORIGIN.split(",") if o.strip()]
        if "http://127.0.0.1:3000" not in origins and "http://localhost:3000" in origins:
            origins.append("http://127.0.0.1:3000")
        return origins


settings = Settings()
