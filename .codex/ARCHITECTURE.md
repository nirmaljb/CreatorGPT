# Architecture

## Stack

- Frontend: Next.js, React, TypeScript.
- Backend: FastAPI.
- Orchestration: LangGraph.
- LLM: Groq `llama-3.3-70b-versatile` for Phase 1 testing.
- Embeddings: FastEmbed `BAAI/bge-small-en-v1.5`.
- Vector DB: Qdrant Cloud.
- Relational DB: Neon Postgres.
- Extraction: `yt-dlp`, `youtube-transcript-api`, `faster-whisper`.

## Runtime Flow

1. `POST /ingest` validates two video inputs and creates a Postgres session.
2. Ingestion runs in a FastAPI background task.
3. Metadata for both videos is scraped and stored first.
4. Per-video transcript/vector work runs concurrently.
5. YouTube tries captions first; unavailable captions fall back to audio download plus Whisper.
6. Instagram uses audio download plus Whisper.
7. Transcript chunks are embedded and stored in Qdrant with payload filters.
8. `POST /chat` loads metadata/history from Postgres, retrieves transcript chunks from Qdrant, and streams a Groq answer.

## Database Schema

### `sessions`

- `id`
- `status`
- `error_message`
- `current_step`
- `progress_percent`
- `created_at`
- `updated_at`

### `video_metadata`

- `session_id`
- `video_id`
- `url`
- `platform`
- `creator`
- `creator_followers`
- `views`
- `likes`
- `comments`
- `hashtags`
- `upload_date`
- `duration_seconds`
- `engagement_rate`

### `chat_messages`

- `session_id`
- `role`
- `content`
- `sources`
- `created_at`

## Vector Payload

Qdrant chunks include:

- `session_id`
- `video_id`
- `chunk_index`
- `text`
- `start_time`
- `end_time`
- `is_hook`
- `engagement_rate`
- `creator`
- `url`
- `source_tag`
- `transcript_source`

Payload indexes are created for `session_id`, `video_id`, and `is_hook`.

## APIs

- `GET /health`: checks API, Postgres, and Qdrant.
- `POST /ingest`: accepts two video inputs and returns `session_id`.
- `GET /status/{session_id}`: returns status, progress, errors, and metadata.
- `GET /messages/{session_id}`: returns persisted chat history.
- `POST /chat`: streams SSE events for sources, tokens, done, or errors.

## Auth

No auth in Phase 1. This is a single-user assignment demo. Production would add tenant/user auth before exposing stored sessions.

## Deployment Notes

- Backend needs `GROQ_API_KEY`, `DATABASE_URL`, `QDRANT_URL`, and `QDRANT_API_KEY`.
- `ffmpeg` is required for Whisper fallback.
- Runtime audio is written outside the repo by default to avoid reload loops.
- For dev reload, use `uvicorn backend.app.main:app --reload --reload-dir backend/app`.
