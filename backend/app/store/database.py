from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import get_settings
from backend.app.store.models import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _normalize_database_url(url: str) -> str:
    if url.startswith("postgres://"):
        return "postgresql+psycopg://" + url.removeprefix("postgres://")
    if url.startswith("postgresql://"):
        return "postgresql+psycopg://" + url.removeprefix("postgresql://")
    return url


def get_engine() -> Engine:
    global _engine
    if _engine is None:
        settings = get_settings()
        if not settings.database_url:
            raise RuntimeError("DATABASE_URL is not configured")
        _engine = create_engine(_normalize_database_url(settings.database_url), pool_pre_ping=True)
    return _engine


def get_session_factory() -> sessionmaker[Session]:
    global _session_factory
    if _session_factory is None:
        _session_factory = sessionmaker(bind=get_engine(), autoflush=False, expire_on_commit=False)
    return _session_factory


@contextmanager
def db_session() -> Iterator[Session]:
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    Base.metadata.create_all(bind=get_engine())
    ensure_session_progress_columns()
    ensure_video_ingestion_columns()


def ensure_session_progress_columns() -> None:
    with get_engine().begin() as conn:
        conn.execute(text("alter table sessions add column if not exists current_step text not null default 'Queued'"))
        conn.execute(text("alter table sessions add column if not exists progress_percent integer not null default 0"))


def ensure_video_ingestion_columns() -> None:
    with get_engine().begin() as conn:
        conn.execute(text("alter table video_metadata add column if not exists raw_metadata jsonb"))
        conn.execute(
            text(
                "alter table video_metadata "
                "add column if not exists ingest_status varchar(32) not null default 'queued'"
            )
        )
        conn.execute(text("alter table video_metadata add column if not exists video_error_message text"))
        conn.execute(
            text(
                "alter table video_metadata "
                "add column if not exists transcript_source varchar(32) not null default 'unavailable'"
            )
        )
        conn.execute(text("alter table video_metadata add column if not exists chunk_count integer not null default 0"))
        conn.execute(text("alter table video_metadata add column if not exists cache_key varchar(128)"))
        conn.execute(
            text("alter table video_metadata add column if not exists metadata_cached boolean not null default false")
        )
        conn.execute(
            text("alter table video_metadata add column if not exists transcript_cached boolean not null default false")
        )


def health_check() -> bool:
    with get_engine().connect() as conn:
        conn.execute(text("select 1"))
    return True
