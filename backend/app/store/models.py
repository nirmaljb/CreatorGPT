from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("google_sub", name="uq_users_google_sub"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    google_sub: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    email: Mapped[str | None] = mapped_column(String(320), nullable=True, index=True)
    email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class OAuthStateModel(Base):
    __tablename__ = "oauth_states"

    state_hash: Mapped[str] = mapped_column(String(128), primary_key=True)
    code_verifier: Mapped[str] = mapped_column(String(128), nullable=False)
    redirect_uri: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    consumed_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class OAuthTokenModel(Base):
    __tablename__ = "oauth_tokens"
    __table_args__ = (UniqueConstraint("user_id", "provider", name="uq_oauth_tokens_user_provider"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(64), nullable=False, default="google")
    encrypted_refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    granted_scopes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    missing_scopes: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    connection_status: Mapped[str] = mapped_column(String(32), nullable=False, default="reconnect_required")
    reconnect_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    last_verified_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ServerSessionModel(Base):
    __tablename__ = "server_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    session_token_hash: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    csrf_token_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    expires_at = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    revoked_at = mapped_column(DateTime(timezone=True), nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_seen_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class SessionModel(Base):
    __tablename__ = "sessions"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    status: Mapped[str] = mapped_column(String(32), nullable=False, default="processing")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    error: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    current_step: Mapped[str] = mapped_column(Text, nullable=False, default="Queued")
    progress_percent: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class SessionUsageLedgerModel(Base):
    __tablename__ = "session_usage_ledger"

    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id"), primary_key=True)
    video_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    transcribed_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    transcript_source: Mapped[str] = mapped_column(String(128), nullable=False, default="unavailable")
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    embedding_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chat_prompt_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chat_completion_tokens: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    llm_model: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    embedding_model: Mapped[str] = mapped_column(String(128), nullable=False, default="")
    cache_hit: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_miss: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class VideoMetadataModel(Base):
    __tablename__ = "video_metadata"
    __table_args__ = (UniqueConstraint("session_id", "video_id", name="uq_video_per_session"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id"), nullable=False, index=True)
    video_id: Mapped[str] = mapped_column(String(1), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    creator: Mapped[str] = mapped_column(Text, nullable=False, default="unknown")
    creator_followers: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    views: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    likes: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    comments: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    hashtags: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    upload_date: Mapped[str | None] = mapped_column(String(32), nullable=True)
    duration_seconds: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    engagement_rate: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    raw_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    ingest_status: Mapped[str] = mapped_column(String(32), nullable=False, default="queued")
    video_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    video_error: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    transcript_source: Mapped[str] = mapped_column(String(32), nullable=False, default="unavailable")
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    cache_key: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    metadata_cached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    transcript_cached: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class ChatMessageModel(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(String(64), ForeignKey("sessions.id"), nullable=False, index=True)
    role: Mapped[str] = mapped_column(String(16), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    sources: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ExtractionCacheModel(Base):
    __tablename__ = "extraction_cache"

    cache_key: Mapped[str] = mapped_column(String(128), primary_key=True)
    platform: Mapped[str] = mapped_column(String(32), nullable=False)
    url: Mapped[str] = mapped_column(Text, nullable=False)
    raw_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    normalized_metadata: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    transcript_words: Mapped[list[dict] | None] = mapped_column(JSON, nullable=True)
    transcript_source: Mapped[str] = mapped_column(String(32), nullable=False, default="unavailable")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
