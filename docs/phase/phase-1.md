# Phase 1 — Thin Vertical Slice

## Scope

Phase 1 builds the first complete demoable version of the RAG chatbot. The goal is a working vertical slice, not a polished production system.

Included in this phase:

- FastAPI backend with ingest, status, health, messages, and streaming chat endpoints.
- Next.js frontend with two configurable video URL inputs, progress state, metadata cards, and chat.
- Background ingestion that returns a `session_id` immediately.
- Metadata extraction for two videos.
- Engagement-rate calculation.
- Transcript extraction using YouTube captions when available and Whisper fallback otherwise.
- Transcript chunking, embedding, and Qdrant storage.
- Durable session, metadata, and chat history storage in Neon Postgres.
- LangGraph retrieval path that loads metadata from Postgres and transcript chunks from Qdrant.
- Real SSE streaming from Groq.
- Source citations for metadata and transcript chunks.

Out of scope for this phase:

- Auth and multi-tenant permissions.
- Durable job queue.
- Redis.
- Hybrid retrieval, reranking, and query classification beyond simple routing helpers.
- Production observability.
- CI and provider-mocked test suite.

## Technologies Used

- Frontend: Next.js, React, TypeScript, CSS.
- Backend: FastAPI, Pydantic, SQLAlchemy.
- Orchestration: LangGraph.
- Chat LLM: Groq `llama-3.3-70b-versatile`.
- Embeddings: FastEmbed with `BAAI/bge-small-en-v1.5`.
- Vector DB: Qdrant Cloud with cosine vectors and payload filters.
- Relational DB: Neon Postgres.
- Metadata/audio extraction: `yt-dlp`.
- YouTube captions: `youtube-transcript-api`.
- Whisper fallback: `faster-whisper`.
- Runtime media support: `ffmpeg`.

## User Flow At This Point

1. User opens the Next.js UI.
2. User enters two video URLs.
3. User selects the platform for each URL: YouTube or Instagram.
4. Frontend calls `POST /ingest`.
5. Backend creates a session in Postgres and returns `session_id` immediately.
6. Frontend stores the session ID and polls `GET /status/{session_id}` with adaptive delays.
7. Backend scrapes and stores metadata for both videos first.
8. Frontend renders available metadata cards while transcript work continues.
9. Backend extracts transcripts, chunks them, embeds chunks, and upserts them to Qdrant.
10. Backend marks the session `ready`.
11. User asks a question in chat.
12. Backend streams a cited answer through `POST /chat`.

## Program Flow

### Ingest Flow

1. `POST /ingest` accepts:

   ```json
   {
     "videos": [
       { "video_id": "A", "platform": "youtube", "url": "..." },
       { "video_id": "B", "platform": "instagram", "url": "..." }
     ]
   }
   ```

2. Backend validates that exactly two videos resolve to Video A and Video B.
3. Backend creates a `sessions` row with:
   - `status = processing`
   - `current_step = Queued`
   - `progress_percent = 0`
4. FastAPI background task starts ingestion.
5. Metadata pass runs first for both videos:
   - `yt-dlp` extracts platform, creator, views, likes, comments, follower count, hashtags, upload date, and duration.
   - Engagement rate is computed as `(likes + comments) / views * 100`.
   - Metadata is upserted into `video_metadata`.
6. Transcript/vector pass runs concurrently per video:
   - YouTube first tries `youtube-transcript-api`.
   - If captions fail or are unavailable, YouTube falls back to `yt-dlp` audio download plus `faster-whisper`.
   - Instagram goes directly to audio download plus `faster-whisper`.
   - Long videos are capped to `MAX_VIDEO_SECONDS`.
7. Chunker builds sliding-window chunks:
   - about 60 words
   - 12-word overlap
   - source tags
   - `is_hook = start_time < 5.0`
8. FastEmbed embeds chunks.
9. Qdrant stores vectors with payload fields:
   - `session_id`
   - `video_id`
   - `chunk_index`
   - `start_time`
   - `end_time`
   - `is_hook`
   - `source_tag`
   - `transcript_source`
10. Backend marks session `ready`.

### Status Flow

1. Frontend polls `GET /status/{session_id}` while status is `processing`.
2. Response includes:
   - session status
   - error message if failed
   - current step
   - progress percent
   - metadata rows
3. Polling is adaptive:
   - faster early polling while metadata appears
   - slower polling during long transcript work
4. The progress bar reflects persisted Postgres state, not frontend-only state.

### Chat Flow

1. Frontend sends `POST /chat` with `session_id` and user message.
2. Backend rejects chat until session is `ready`.
3. LangGraph loads:
   - chat history from Postgres
   - metadata from Postgres
   - transcript chunks from Qdrant
4. Prompt is built with:
   - `[METADATA]`
   - `[TRANSCRIPT CHUNKS]`
   - recent chat history
   - user question
5. Groq streams the answer token-by-token.
6. Backend emits SSE events:
   - `sources`
   - `token`
   - `done`
   - `error`
7. Assistant response and source list are persisted in `chat_messages`.

## Component Flow

### Frontend

- `frontend/src/app/page.tsx`
  - Owns URL inputs, platform selectors, session state, progress display, metadata cards, chat history, and SSE parsing.
  - Stores the current session ID in local storage for refresh recovery.

- `frontend/src/app/globals.css`
  - Provides the minimal app layout, cards, progress bar, messages, source chips, and responsive behavior.

### Backend API

- `backend/app/main.py`
  - Creates FastAPI app.
  - Configures CORS.
  - Runs startup checks.
  - Exposes health, ingest, status, messages, and chat endpoints.

- `backend/app/api/schemas.py`
  - Defines the ingest and chat request contracts.
  - Supports both new generic `videos` input and legacy `youtube_url`/`instagram_url` input.

### Ingestion

- `backend/app/ingest/metadata.py`
  - Extracts metadata through `yt-dlp`.
  - Normalizes missing values.
  - Computes engagement rate.

- `backend/app/ingest/youtube_transcript.py`
  - Extracts YouTube video IDs from common URL shapes.
  - Fetches captions when available.
  - Converts caption segments into `{text, start, end}` word-like records.

- `backend/app/ingest/downloader.py`
  - Downloads audio with `yt-dlp`.
  - Caps long videos to the configured max transcript window.
  - Writes runtime audio outside the repo by default.

- `backend/app/ingest/transcriber.py`
  - Loads `faster-whisper`.
  - Produces word-level timestamp records.

- `backend/app/ingest/chunker.py`
  - Converts transcript words into overlapping chunks.
  - Adds timestamps, hook flags, engagement rate, source tags, and transcript source.

- `backend/app/ingest/pipeline.py`
  - Coordinates ingestion.
  - Stores metadata first.
  - Runs transcript/vector work concurrently.
  - Updates persisted progress.
  - Handles cleanup and failure state.

### Storage

- `backend/app/store/models.py`
  - Defines SQLAlchemy models for sessions, video metadata, and chat messages.

- `backend/app/store/postgres.py`
  - Encapsulates session status, progress, metadata, and chat-message reads/writes.

- `backend/app/store/vector.py`
  - Manages Qdrant client, collection creation, dimension validation, payload indexes, embeddings, upsert, and retrieval.

### RAG

- `backend/app/rag/graph.py`
  - LangGraph retrieval flow.
  - Loads history, metadata, and transcript chunks.

- `backend/app/rag/prompt.py`
  - Builds the grounded prompt.
  - Formats metadata and transcript chunks with source tags.

- `backend/app/rag/chat_client.py`
  - Wraps Groq streaming.

- `backend/app/rag/service.py`
  - Produces SSE events and persists chat messages.

## Data Ownership

- Postgres is the source of truth for:
  - session status
  - progress
  - video metadata
  - chat history

- Qdrant is the source of truth for:
  - embedded transcript chunks
  - semantic transcript retrieval
  - hook chunk retrieval

- Metadata is duplicated in Qdrant payloads only for retrieval context and citation support. Canonical metadata answers should come from Postgres.

## Decision Tradeoffs

- FastAPI over Node backend:
  - Better local support for `yt-dlp`, `faster-whisper`, FastEmbed, and LangGraph.

- Groq over OpenAI for Phase 1 chat:
  - Faster and lower-cost for demo testing.
  - Later OpenAI migration remains isolated behind provider wrappers.

- FastEmbed/BGE over paid embedding APIs:
  - Lower cost and no embedding API dependency.
  - Retrieval quality may be lower than OpenAI embeddings, but is good enough for short transcript chunks.

- Qdrant Cloud over local Docker:
  - More realistic cloud demo.
  - Requires payload indexes for filtered search.

- Neon Postgres over SQLite:
  - Durable persisted state that survives refreshes and looks closer to production.
  - Slightly more setup through environment configuration.

- SQLAlchemy `create_all` over migrations:
  - Faster for Phase 1.
  - Later schema churn should move to Alembic migrations.

- YouTube captions before Whisper:
  - Much faster and cheaper for YouTube.
  - Captions may be unavailable or imperfect, so Whisper fallback remains.

- Whisper fallback for Instagram:
  - More reliable than depending on platform transcript support.
  - Slower and requires local compute.

- Transcript cap through `MAX_VIDEO_SECONDS`:
  - Controls demo latency and cost.
  - Full long-form analysis is deferred.

- Concurrent per-video transcript/vector work:
  - Greatly reduces two-video ingest time.
  - Requires thread-safe lazy initialization for shared clients/models.

- FastAPI background task over durable queue:
  - Simple enough for the assignment demo.
  - Production should use a real job queue for retries, cancellation, and worker isolation.

- SSE through POST fetch instead of `EventSource`:
  - Allows request body with `session_id` and message.
  - Requires manual SSE parsing on the frontend.

## Current Acceptance State

- Backend imports and compiles.
- Frontend production build passes.
- Health checks pass against Neon and Qdrant.
- Live ingest for two YouTube videos completed in about 14 seconds using YouTube captions.
- Qdrant stored chunks for both videos.
- Chat streamed an engagement-rate answer with metadata citations.