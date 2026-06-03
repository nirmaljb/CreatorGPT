from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    groq_api_key: str = Field(default="", alias="GROQ_API_KEY")
    groq_chat_model: str = Field(default="llama-3.3-70b-versatile", alias="GROQ_CHAT_MODEL")
    groq_transcription_model: str = Field(default="whisper-large-v3", alias="GROQ_TRANSCRIPTION_MODEL")

    database_url: str = Field(default="", alias="DATABASE_URL")

    qdrant_url: str = Field(default="", alias="QDRANT_URL")
    qdrant_api_key: str = Field(default="", alias="QDRANT_API_KEY")
    qdrant_collection: str = Field(default="creator_video_chunks", alias="QDRANT_COLLECTION")
    require_qdrant_on_startup: bool = Field(default=False, alias="REQUIRE_QDRANT_ON_STARTUP")
    qdrant_check_compatibility: bool = Field(default=False, alias="QDRANT_CHECK_COMPATIBILITY")

    embedding_provider: str = Field(default="fastembed", alias="EMBEDDING_PROVIDER")
    embedding_model: str = Field(default="BAAI/bge-small-en-v1.5", alias="EMBEDDING_MODEL")
    embedding_dimensions: int = Field(default=384, alias="EMBEDDING_DIMENSIONS")

    max_video_seconds: int = Field(default=600, alias="MAX_VIDEO_SECONDS", ge=1)
    max_concurrent_ingestions: int = Field(default=2, alias="MAX_CONCURRENT_INGESTIONS", ge=1)
    max_chunks_per_video: int = Field(default=120, alias="MAX_CHUNKS_PER_VIDEO", ge=1)
    max_chat_history_messages: int = Field(default=12, alias="MAX_CHAT_HISTORY_MESSAGES", ge=0)
    max_retrieved_chunks: int = Field(default=8, alias="MAX_RETRIEVED_CHUNKS", ge=1)
    max_sessions_per_ip_per_hour: int = Field(default=20, alias="MAX_SESSIONS_PER_IP_PER_HOUR", ge=1)
    ingest_stale_seconds: int = Field(default=900, alias="INGEST_STALE_SECONDS")
    tmp_dir: str = Field(default="/private/tmp/creator-rag", alias="TMP_DIR")
    force_refresh: bool = Field(default=False, alias="FORCE_REFRESH")
    ytdlp_cookies_path: str = Field(default="", alias="YTDLP_COOKIES_PATH")
    ytdlp_cookies_from_browser: str = Field(default="", alias="YTDLP_COOKIES_FROM_BROWSER")

    cors_origins: str = Field(default="http://localhost:3000", alias="CORS_ORIGINS")
    cors_origin_regex: str = Field(default="", alias="CORS_ORIGIN_REGEX")

    @property
    def cors_origin_list(self) -> list[str]:
        origins = {origin.strip().rstrip("/") for origin in self.cors_origins.split(",") if origin.strip()}
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
