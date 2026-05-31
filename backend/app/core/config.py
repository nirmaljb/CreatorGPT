from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_chat_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_CHAT_MODEL")

    database_url: str = Field(default="", alias="DATABASE_URL")

    qdrant_url: str = Field(default="", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="creator_video_chunks", alias="QDRANT_COLLECTION")

    embedding_provider: str = Field(default="fastembed", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5", alias="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=384, alias="EMBEDDING_DIMENSIONS")

    max_video_seconds: int = Field(default=600, alias="MAX_VIDEO_SECONDS")
    whisper_model_size: str = Field(default="base", alias="WHISPER_MODEL_SIZE")
    tmp_dir: str = Field(default="/private/tmp/creator-rag", alias="TMP_DIR")
    force_refresh: bool = Field(default=False, alias="FORCE_REFRESH")

    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")

    @property
    def cors_origin_list(self) -> list[str]:
        origins = {origin.strip() for origin in self.cors_origins.split(",") if origin.strip()}
        origins.update(
            {
                "http://localhost:3000",
                "http://localhost:3001",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:3001",
            }
        )
        return sorted(origins)

    @property
    def effective_tmp_dir(self) -> str:
        if self.tmp_dir.strip() in {"tmp", "./tmp"}:
            return "/private/tmp/creator-rag"
        return self.tmp_dir


@lru_cache
def get_settings() -> Settings:
    return Settings()
