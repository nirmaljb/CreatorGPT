# Agent Notes

## Operating Workflow

- Before implementing any feature or fix, read `AGENTS.md` first and then read `.codex/Progress.md`.
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

- Add rules-first LangGraph routing for metadata, transcript, hook, mixed comparison, improvement, and follow-up questions.
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
- Groq `whisper-large-v3` for hosted Whisper transcription with word timestamps.
- `youtube-transcript-api` for YouTube caption fast-path before Whisper fallback.
- Minimal UI with two video cards and a chat panel.

## Developer Workflow

- All meaningful changes must update `Progress.md`.
- All architectural/provider/schema changes must update `Agents.md` and the corresponding docs such as `ARCHITECTURE.md`, `PLANS.md`, `PRODUCT_SPEC.md`
- Run `python scripts/eval_assignment_questions.py --session-id <id>` before making retrieval, chunking, embedding, or routing optimizations so changes are measured against the required questions.
- Run `make ci` before opening a PR when practical; required CI must stay provider-mocked and must not depend on real Groq, Qdrant Cloud, Neon, YouTube, or Instagram.
- External services must be abstracted behind provider wrappers so tests do not require Groq, Neon, Qdrant Cloud, YouTube, or Instagram.

## Coding rules

- Never hardcode secrets.
- Prefer server-side checks for authorization.
- Add tests for new behavior.

## Do not

- Do not rewrite unrelated files.
- Do not introduce new libraries without explaining why.

## Decisions And Tradeoffs

- Backend is FastAPI because Python has the cleanest path for `yt-dlp`, Groq audio transcription, LangGraph, Qdrant, and batch ingestion.
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
- Citation text must use exact source tags such as `[Video A metadata]`; do not emit wrapper citations like `[source_tag: ...]` or non-source tags like `[POSTGRES METADATA TOOL RESULTS]`.
- Missing Instagram metadata is expected. Unknown strings stay `unknown`; missing counts default to `0` in stored integer columns for compatibility, but availability flags decide whether UI and chat render them as `unavailable`.
- Engagement-rate comparison is incomplete when a video's view count is unavailable. Do not declare a winner from a missing denominator.
- Status and chat context expose metric availability flags so missing extractor counts are rendered as `unavailable` instead of treated as real zeroes.
- Phase 1 uses SQLAlchemy `create_all` at startup instead of Alembic migrations to reduce setup overhead. If schema churn starts, add migrations in a later phase.
- Ingestion runs as a FastAPI background task. Metadata is processed first for both videos, then per-video transcript/vector work runs concurrently. A production version should move this to a durable queue.
- Backend startup validates Postgres and Qdrant by creating tables and ensuring the vector collection. This is fail-fast by design when `.env` is missing or cloud services are unavailable.
- The chat path uses LangGraph for durable retrieval orchestration, then streams Groq tokens through a small provider wrapper so OpenAI can replace Groq later with minimal changes.
- Compare questions that mention both Video A and Video B retrieve chunks from both videos; single-video questions stay filtered to that video.
- Numeric and creator metadata questions must bypass Qdrant retrieval and use typed Postgres metadata tools only: `get_video_metrics`, `get_creator_info`, `get_engagement_comparison`, and `get_session_video_summary`.
- Phase 2 uses deterministic route labels: `METADATA_ONLY`, `TRANSCRIPT_ONLY`, `HOOK_COMPARISON`, `MIXED_COMPARISON`, `IMPROVEMENT_SUGGESTION`, and `FOLLOW_UP`.
- The Phase 2 router is rules-first, not LLM-classified. This keeps assignment routing deterministic, cheap, and unit-testable; add an LLM classifier only if evals prove the rules are insufficient.
- `FOLLOW_UP` handling is intentionally minimal: resolve obvious references like "their", "that video", and "what about B" from recent chat history, then re-route the resolved question.
- Semantic transcript questions use Qdrant retrieval. Mixed comparison and improvement questions use the Postgres metadata tools plus Qdrant retrieval.
- Mixed comparison answers must cite transcript chunk evidence when chunks are retrieved, not only metadata metrics.
- Assignment evals are run through `scripts/eval_assignment_questions.py`; reusable logic lives in `backend.evals.assignment_eval` for later mocked CI coverage.
- Required CI runs backend Ruff lint, backend Pytest tests, frontend ESLint, frontend TypeScript typecheck, frontend build, markdown lint, and a provider-mocked smoke test.
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
- Phase 1 does not implement retry. A browser refresh starts a clean frontend state instead of restoring the previous `session_id`; a later retry flow should be explicit and should not silently resume a stale failed session.
- `GET /status/{session_id}` marks long-stale `processing` sessions as `failed` after `INGEST_STALE_SECONDS`, so stopped background tasks surface as readable frontend errors instead of remaining stuck forever.
- The frontend treats network loss separately from ingestion failure. Offline/API-unreachable polling pauses with a visible connection message and resumes status loading when the browser comes back online.
- YouTube ingestion first tries `youtube-transcript-api` captions and normalizes captions into the same `{text, start, end}` shape as Whisper output. If captions are unavailable or the caption API fails, ingestion falls back to `yt-dlp` audio extraction plus Groq `whisper-large-v3`.
- YouTube caption transcripts are not capped by `MAX_VIDEO_SECONDS`; long YouTube videos can ingest through captions without Whisper. `MAX_VIDEO_SECONDS` only limits audio download/Whisper fallback.
- Per-video transcript/vector work now runs concurrently with `asyncio.gather` after both metadata rows are stored. Blocking operations run through `asyncio.to_thread`.
- Qdrant payload indexes are created at startup for `session_id`, `video_id`, and `is_hook` because Qdrant Cloud requires indexed payload fields for filtered search.
- Runtime audio uses `Settings.effective_tmp_dir`; legacy `TMP_DIR=tmp` is redirected to `/private/tmp/creator-rag` to avoid `uvicorn --reload` watching generated media files.
- FastEmbed/Qdrant client initialization is lock-protected for threaded ingestion.
- Ingestion is now organized behind platform-specific extractor classes. YouTube owns the captions-first path and Instagram owns the Whisper audio path.
- Terminal ingest sessions use `completed` status. `/chat` still accepts older `ready` sessions for compatibility.
- Video metadata rows store raw extractor metadata, per-video ingest status, failure messages, transcript source, chunk count, and cache flags.
- Transcript source is recorded as `captions`, `whisper`, or `unavailable` in Postgres and chunk payloads.
- Extraction cache is stored in Postgres by platform, URL, cache version, and `MAX_VIDEO_SECONDS` so repeated demos reuse real extractor output. Cache version `extract-v3` avoids reusing older capped-caption or local-Whisper entries. `FORCE_REFRESH=true` bypasses cache reads and forces fresh extraction.
- Ingestion must fail visibly for real extractor/download/transcription errors; do not silently fall back to fake metadata, fake transcripts, or fabricated chunks.

## Source Citation Format

- Metadata: `[Video A metadata]`
- Transcript chunk: `[Video A, chunk 3, 00:12-00:27]`

## Runtime Assumptions

- Required external services and keys are provided in `.env`.
- `ffmpeg` must be installed locally for reliable `yt-dlp` audio extraction.
- Instagram extraction may require cookies depending on the URL/account availability. Phase 1 reports a clear failure instead of bypassing platform restrictions.
