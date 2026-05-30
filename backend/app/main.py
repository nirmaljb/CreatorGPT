import uuid

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.app.api.schemas import ChatRequest, IngestRequest, IngestResponse
from backend.app.core.config import get_settings
from backend.app.ingest.pipeline import ingest_session
from backend.app.rag.service import stream_rag_response
from backend.app.store import database
from backend.app.store.postgres import create_session, get_chat_messages, get_session
from backend.app.store.vector import ensure_collection, health_check as qdrant_health_check

settings = get_settings()

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
    database.init_db()
    ensure_collection()


@app.get("/health")
def health() -> dict:
    return {
        "api": True,
        "postgres": database.health_check(),
        "qdrant": qdrant_health_check(),
    }


@app.post("/ingest", response_model=IngestResponse)
def ingest(payload: IngestRequest, background_tasks: BackgroundTasks) -> IngestResponse:
    session_id = str(uuid.uuid4())
    create_session(session_id)
    background_tasks.add_task(
        ingest_session,
        session_id,
        payload.youtube_url,
        payload.instagram_url,
    )
    return IngestResponse(session_id=session_id, status="processing")


@app.get("/status/{session_id}")
def status(session_id: str) -> dict:
    row = get_session(session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return row


@app.get("/messages/{session_id}")
def messages(session_id: str) -> dict:
    if get_session(session_id) is None:
        raise HTTPException(status_code=404, detail="Session not found")
    return {"messages": get_chat_messages(session_id, limit=50)}


@app.post("/chat")
def chat(payload: ChatRequest) -> StreamingResponse:
    row = get_session(payload.session_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Session not found")
    if row["status"] != "ready":
        raise HTTPException(status_code=409, detail=f"Session is {row['status']}, not ready")
    return StreamingResponse(
        stream_rag_response(payload.session_id, payload.message),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
