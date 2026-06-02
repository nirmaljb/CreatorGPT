import inspect
import logging
import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.app.api.schemas import ChatRequest, IngestRequest, IngestResponse
from backend.app.core.backpressure import (
    active_ingestions,
    check_session_rate_limit,
    client_ip_from_request,
    release_ingest_slot,
    try_acquire_ingest_slot,
)
from backend.app.core.config import get_settings
from backend.app.core.logging import configure_logging
from backend.app.ingest.pipeline import ingest_session
from backend.app.rag.service import stream_rag_response
from backend.app.store import database
from backend.app.store.postgres import create_session, fail_stale_processing_session, get_chat_messages, get_session
from backend.app.store.vector import ensure_collection
from backend.app.store.vector import health_check as qdrant_health_check

configure_logging()
settings = get_settings()
logger = logging.getLogger(__name__)

app = FastAPI(title="Creator Video RAG Comparator")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    logger.info("Starting backend startup checks")
    database.init_db()
    try:
        ensure_collection()
    except Exception as exc:
        message = (
            "Qdrant startup validation failed. The API will start in degraded mode with qdrant=false in /health. "
            "Ingestion and transcript retrieval still require Qdrant and will fail visibly until QDRANT_URL, "
            "QDRANT_API_KEY, and network/DNS connectivity are fixed. Set REQUIRE_QDRANT_ON_STARTUP=true to fail "
            f"startup instead. Error: {exc}"
        )
        if settings.require_qdrant_on_startup:
            raise RuntimeError(message) from exc
        logger.warning(message)
    logger.info("Backend startup checks completed")


def _runtime_limits() -> dict:
    return {
        "max_video_seconds": settings.max_video_seconds,
        "max_concurrent_ingestions": settings.max_concurrent_ingestions,
        "max_chunks_per_video": settings.max_chunks_per_video,
        "max_chat_history_messages": settings.max_chat_history_messages,
        "max_retrieved_chunks": settings.max_retrieved_chunks,
        "max_sessions_per_ip_per_hour": settings.max_sessions_per_ip_per_hour,
    }


def _run_ingest_with_slot(session_id: str, videos: list[dict]) -> None:
    try:
        result = ingest_session(session_id, videos)
        if inspect.isawaitable(result):
            import asyncio

            asyncio.run(result)
    finally:
        release_ingest_slot()


@app.get("/health")
def health() -> dict:
    postgres_ok = False
    qdrant_ok = False
    try:
        postgres_ok = database.health_check()
    except Exception:
        logger.exception("Postgres health check failed")
    try:
        qdrant_ok = qdrant_health_check()
    except Exception as exc:
        logger.warning("Qdrant health check failed: %s", exc)
    return {
        "api": True,
        "postgres": postgres_ok,
        "qdrant": qdrant_ok,
    }


@app.get("/config")
def config() -> dict:
    return {
        "limits": _runtime_limits(),
        "active_ingestions": active_ingestions(),
    }


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, background_tasks: BackgroundTasks, request: Request) -> IngestResponse:
    session_id = str(uuid.uuid4())
    videos = [video.model_dump() for video in payload.normalized_videos()]
    client_ip = client_ip_from_request(request)
    if not try_acquire_ingest_slot(settings.max_concurrent_ingestions):
        raise HTTPException(
            status_code=429,
            detail=(
                "Too many ingestions are already running. "
                f"Limit: {settings.max_concurrent_ingestions} concurrent ingestion(s)."
            ),
        )

    rate_allowed, retry_after_seconds, attempts = check_session_rate_limit(
        client_ip,
        settings.max_sessions_per_ip_per_hour,
    )
    if not rate_allowed:
        release_ingest_slot()
        raise HTTPException(
            status_code=429,
            detail=(
                "Session rate limit reached for this IP. "
                f"Limit: {settings.max_sessions_per_ip_per_hour} session(s) per hour."
            ),
            headers={"Retry-After": str(retry_after_seconds)},
        )

    logger.info(
        "Accepted ingest request session_id=%s client_ip=%s attempts_in_last_hour=%s videos=%s",
        session_id,
        client_ip,
        attempts,
        videos,
    )
    try:
        create_session(session_id)
    except Exception:
        release_ingest_slot()
        raise
    background_tasks.add_task(
        _run_ingest_with_slot,
        session_id,
        videos,
    )
    return IngestResponse(session_id=session_id, status="processing")


@app.get("/status/{session_id}")
def status(session_id: str) -> dict:
    row = get_session(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if row["status"] == "processing":
        fail_stale_processing_session(session_id, settings.ingest_stale_seconds)
        row = get_session(session_id)
        if row is None:
            raise HTTPException(status_code=404, detail="Session not found")
    logger.info(
        "Status response session_id=%s status=%s step=%s progress=%s metadata_count=%s",
        session_id,
        row["status"],
        row.get("current_step"),
        row.get("progress_percent"),
        len(row.get("metadata") or []),
    )
    return row


@app.get("/messages/{session_id}")
def messages(session_id: str) -> dict:
    if get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"messages": get_chat_messages(session_id, limit=settings.max_chat_history_messages)}


@app.post("/chat")
def chat(payload: ChatRequest) -> StreamingResponse:
    row = get_session(payload.session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if row["status"] not in {"ready", "completed"}:
        raise HTTPException(status_code=409, detail=f"Session is {row['status']}, not completed")
    return StreamingResponse(
        stream_rag_response(payload.session_id, payload.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
