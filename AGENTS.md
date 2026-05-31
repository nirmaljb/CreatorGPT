# Agent Notes

## Operating Workflow

- Before implementing any feature or fix, read `.codex/Agents.md` first and then read `.codex/Progress.md`.
- After each meaningful implementation chunk, update `.codex/Progress.md` with what changed, what was verified, and what remains.
- Update this file when a planning or implementation decision changes the architecture, provider choices, schema, interfaces, or developer workflow.
- For large work, create or update the relevant milestone in `.codex/PLANS.md` before implementation.
- Keep phase documentation current in `docs/phase/phase-<number>.md`. Phase files start with scope only; as each phase progresses, expand the corresponding file with technologies, program flow, component flow, and tradeoffs in the same work chunk.

## Product Goal

Build a full-stack RAG chatbot that compares one YouTube video and one Instagram Reel. The system ingests video URLs, extracts metadata and transcripts, chunks and embeds transcript text, stores chunks in Qdrant, stores durable session/chat/video state in Postgres, and answers creator questions with streaming, cited responses.

## Revised Phase Plan

### Phase 0 — Contracts and Demo Safety

- Define API contracts, DB schema, provider interfaces, env validation, and extraction cache.
- Create README skeleton, Progress.md, and demo script outline.
- Select known-good YouTube and Instagram test URLs.

### Phase 1 — Thin Vertical Slice

- Build FastAPI ingest/status/chat endpoints.
- Return session_id immediately from ingest.
- Run ingestion in background.
- Store sessions, video metadata, transcript chunks, and chat history.
- Store vectors in Qdrant with video_id/session_id payload filters.
- Build minimal Next.js UI with two URL inputs, progress state, and streaming chat.
- Verify one full flow: ingest -> status complete -> chat -> cited answer.

### Phase 2 — Grounded Intelligence

- Add LangGraph routing for numeric, semantic, hook, and recommendation questions.
- Use typed metadata tools instead of a free-form SQL agent.
- Use transcript retrieval only for semantic questions.
- Use first-5-second chunks for hook comparison.
- Add citation validation and an eval script for assignment questions.

### Phase 3 — Product UI

- Add side-by-side video cards with metrics.
- Add citation chips, suggested questions, loading states, and failure states.
- Make the demo path feel fast and obvious.

### Phase 4 — Resilience and Demo Readiness

- Add provider-mocked smoke tests.
- Add markdown linting and CI.
- Finalize README, architecture notes, cost/scaling notes, and Loom script.
- Run clean-clone demo rehearsal before recording.

## Phase 1 Scope

- FastAPI backend.
- Next.js frontend.
- LangGraph orchestration.
- Neon Postgres for durable sessions, video metadata, and chat history.
- Qdrant Cloud for vector search.
- Groq `llama-3.3-70b-versatile` for streaming chat during testing.
- FastEmbed `BAAI/bge-small-en-v1.5` for embeddings during testing.
- `yt-dlp` for metadata and audio download.
- `faster-whisper` for transcription with word timestamps.
- `youtube-transcript-api` for YouTube caption fast-path before Whisper fallback.
- Minimal UI with two video cards and a chat panel.

## Developer Workflow
- All meaningful changes must update `Progress.md`.
- All architectural/provider/schema changes must update `Agents.md` and the corresponding docs such as `ARCHITECTURE.md`, `PLANS.md`, `PRODUCT_SPEC.md`
- External services must be abstracted behind provider wrappers so tests do not require Groq, Neon, Qdrant Cloud, YouTube, or Instagram.


## Coding rules
- Never hardcode secrets.
- Prefer server-side checks for authorization.
- Add tests for new behavior.

## Do not
- Do not rewrite unrelated files.
- Do not introduce new libraries without explaining why.

## Decisions And Tradeoffs

- Backend is FastAPI because Python has the cleanest path for `yt-dlp`, `faster-whisper`, LangGraph, Qdrant, and batch ingestion.
- Frontend is Next.js because it is required by the assignment stack and is fast to ship for a demo.
- Phase 1 uses Groq chat instead of OpenAI chat to keep inference fast and low-cost during testing.
- Phase 1 uses `llama-3.3-70b-versatile` on Groq as the chat model because it gives strong reasoning quality with high streaming throughput.
- Groq is not used for embeddings in Phase 1. The embedding path uses FastEmbed because Groq's production API is focused on chat/audio style inference, while retrieval needs a dedicated embedding model.
- Phase 1 uses `BAAI/bge-small-en-v1.5` via FastEmbed. It is cheap, local, fast, and good enough for short transcript chunks.
- Qdrant collection dimension is `384` for BGE small. This must change if moving to OpenAI `text-embedding-3-small`, which uses `1536`.
- Later OpenAI migration should be isolated to provider wrappers: chat client, embedding client, and Qdrant collection dimensions.
- Neon Postgres replaces SQLite so session status and chat memory survive refreshes and look realistic in the demo.
- Qdrant Cloud replaces local Docker to reduce local setup friction and demonstrate cloud vector infrastructure.
- Reranking, hybrid search, Redis, LangSmith, Sentry, auth, and job queues are intentionally out of Phase 1.
- Responses must cite facts with source tags. Numeric claims should come from Postgres metadata or chunk payloads, not model invention.
- Missing Instagram metadata is expected. Unknown strings stay `unknown`; missing counts default to `0`; unavailable follower counts should be stated as unavailable when needed.
- Phase 1 uses SQLAlchemy `create_all` at startup instead of Alembic migrations to reduce setup overhead. If schema churn starts, add migrations in a later phase.
- Ingestion runs as a FastAPI background task. Metadata is processed first for both videos, then per-video transcript/vector work runs concurrently. A production version should move this to a durable queue.
- Backend startup validates Postgres and Qdrant by creating tables and ensuring the vector collection. This is fail-fast by design when `.env` is missing or cloud services are unavailable.
- The chat path uses LangGraph for durable retrieval orchestration, then streams Groq tokens through a small provider wrapper so OpenAI can replace Groq later with minimal changes.
- The frontend uses `fetch` with a POST body and manually parses SSE because native `EventSource` does not support POST request bodies.
- Frontend config pins `outputFileTracingRoot` to the frontend directory because this machine has another lockfile above the repo and Next.js otherwise infers the wrong root.
- Downloaded audio files are temporary and are deleted after ingestion finishes or fails.
- Phase 1 input is now two generic video slots. Each slot can be marked as YouTube or Instagram in the UI, while defaulting to Video A = YouTube and Video B = Instagram for the assignment demo.
- Videos longer than `MAX_VIDEO_SECONDS` are no longer rejected in Phase 1. The downloader trims ingestion to the first configured window so long videos can still produce hook and early-transcript chunks.
- Ingestion uses a two-pass flow: scrape/store metadata for both videos first, then download/transcribe/embed each video. This makes status responses useful even while long transcription work is still running.
- Ingestion logs are intentionally verbose in development: session ID, video ID, requested platform, metadata counts, duration, audio path, transcription word count, chunk count, Qdrant upsert count, elapsed time, and stack traces on failure.
- Qdrant startup now validates existing collection dimensions against `EMBEDDING_DIMENSIONS` so provider/model swaps fail with a clear error instead of during upsert.
- Development CORS allows local frontend ports 3000 and 3001 because Next.js may move to 3001 when 3000 is already occupied.
- Session status includes persisted progress fields: `current_step` and `progress_percent`. The frontend uses them to show ingestion progress and to poll adaptively instead of using a fixed short interval.
- YouTube ingestion first tries `youtube-transcript-api` captions and normalizes captions into the same `{text, start, end}` shape as Whisper output. If captions are unavailable or the caption API fails, ingestion falls back to `yt-dlp + faster-whisper`.
- YouTube caption transcripts are capped to `MAX_VIDEO_SECONDS`, matching the existing Phase 1 transcript cap for Whisper.
- Per-video transcript/vector work now runs concurrently with `asyncio.gather` after both metadata rows are stored. Blocking operations run through `asyncio.to_thread`.
- Qdrant payload indexes are created at startup for `session_id`, `video_id`, and `is_hook` because Qdrant Cloud requires indexed payload fields for filtered search.
- Runtime audio uses `Settings.effective_tmp_dir`; legacy `TMP_DIR=tmp` is redirected to `/private/tmp/creator-rag` to avoid `uvicorn --reload` watching generated media files.
- FastEmbed/Qdrant client and faster-whisper model initialization are lock-protected for threaded ingestion.

## Source Citation Format

- Metadata: `[Video A metadata]`
- Transcript chunk: `[Video A, chunk 3, 00:12-00:27]`

## Runtime Assumptions

- Required external services and keys are provided in `.env`.
- `ffmpeg` must be installed locally for reliable `yt-dlp` audio extraction.
- Instagram extraction may require cookies depending on the URL/account availability. Phase 1 reports a clear failure instead of bypassing platform restrictions.
