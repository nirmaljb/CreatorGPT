# Plans

## Phase 0 — Contracts and Demo Safety

### Milestones

- Define API contracts for ingest, status, messages, health, and chat.
- Define Postgres schema for sessions, video metadata, extraction cache, and chat history.
- Define provider interfaces for LLM, embeddings, vector storage, and platform-specific transcript extraction.
- Add env validation and `.env.example`.
- Create README skeleton, Progress.md, and demo script outline.
- Select known-good YouTube and Instagram URLs.

### Acceptance Criteria

- A new engineer can understand the intended contracts before reading implementation code.
- Missing env vars fail clearly.
- Demo URLs are known before recording.

## Phase 1 — Thin Vertical Slice

### Milestones

- Build FastAPI ingest/status/chat endpoints.
- Return `session_id` immediately from ingestion.
- Run ingestion in the background.
- Store sessions, video metadata, transcript chunks, and chat history.
- Store raw metadata, transcript source, chunk counts, cache flags, and per-video failure state.
- Cache real extraction results for repeatable demos, with a `FORCE_REFRESH=true` escape hatch.
- Support optional `yt-dlp` cookie configuration for YouTube sign-in or bot-check challenges.
- Store vectors in Qdrant with `video_id` and `session_id` payload filters.
- Build minimal Next.js UI with two URL inputs, progress state, clean refresh behavior, offline handling, and streaming chat.
- Verify one full flow: ingest -> status complete -> chat -> cited answer.

### Acceptance Criteria

- User can ingest two videos from the UI.
- Status reaches `completed` or a readable `failed` state.
- Metadata cards render for both videos when available.
- Per-video status explains platform/caption/download/transcription failures.
- YouTube sign-in or bot-check failures explain the cookie configuration path instead of requiring raw `yt-dlp` debugging.
- API startup can continue when Qdrant Cloud is temporarily unreachable, while `/health` reports `qdrant: false`; deployments can opt into fail-fast Qdrant validation with `REQUIRE_QDRANT_ON_STARTUP=true`.
- Refreshing the frontend starts from a clean state instead of restoring a stale in-progress session.
- Stalled background ingestion is surfaced as failed status after `INGEST_STALE_SECONDS`; automatic retry is deferred.
- Chat streams and cites metadata/chunks.
- Full flow works against live Neon, Qdrant, and Groq credentials.

## Phase 2 — Grounded Intelligence

### Milestones

- Add rules-first LangGraph routing for metadata, transcript, hook, mixed comparison, improvement, and follow-up questions.
- Use typed Postgres metadata tools for numeric and creator/follower questions.
- Use transcript retrieval only for semantic and recommendation questions.
- Restrict hook comparison to first-5-second chunks.
- Add named retrieval policies so comparison questions retrieve balanced Video A and Video B evidence.
- Resolve simple follow-up references from recent chat history, then re-route.
- Add citation validation.
- Expose route and retrieval policy in chat SSE payloads so evals can assert the selected path directly.
- Add a per-session internal usage ledger for transcript seconds, chunk/embedding counts, cache hits/misses, model names, and chat token usage.
- Add runtime backpressure limits for ingest concurrency, per-IP sessions, per-video chunks, chat history, retrieved chunks, and Whisper/audio seconds.
- Add an eval script for the assignment's expected question set before making further retrieval/chunking changes.

### Acceptance Criteria

- Metadata questions do not depend on vector retrieval.
- Numeric and creator questions bypass Qdrant retrieval entirely.
- Hook questions cite hook chunks only.
- Recommendation answers cite transcript evidence and metrics.
- Improvement answers retrieve Video A evidence for what worked and Video B evidence for improvement opportunities.
- Comparison and metadata-augmented routes retrieve `top_k=4` from Video A and `top_k=4` from Video B instead of one global `top_k=8` search.
- Route-aware evals verify expected route, expected retrieval policy, citation shape, numeric values, unavailable metric behavior, vague/open-ended questions, creative synthesis, multi-step prompts, and incorrect-premise questions.
- Usage ledger rows are created for each ingest session and updated after ingestion/chat without requiring real providers in CI.
- Backpressure limits are enforced by backend tests and surfaced to the frontend through `GET /config`.
- Follow-up questions resolve obvious video references without using a full query-rewrite pipeline.
- Eval script passes the assignment's core questions.

## Phase 3 — Product UI

### Milestones

- Improve side-by-side video cards with clearer metrics and unavailable states.
- Add citation chips that map to metadata or chunk sources.
- Add suggested questions for the required demo prompts.
- Add polished loading, progress, empty, and failure states.
- Make the demo path fast and obvious.

### Acceptance Criteria

- A reviewer can run the demo without guessing the next action.
- Failure states explain platform/caption/download problems clearly.
- Citations are visible and readable without opening dev tools.

## Phase 4 — Resilience and Demo Readiness

### Milestones

- Add provider-mocked smoke tests.
- Add root `Makefile` targets for backend lint/tests, frontend lint/typecheck/build, markdown lint, and mocked smoke tests.
- Add pre-commit, Ruff, Pytest, markdown lint, PR template, and GitHub Actions CI.
- Keep required CI provider-mocked only; real Groq, Qdrant Cloud, Neon, YouTube, and Instagram checks stay manual or nightly.
- Add backend Docker deployment support for Render with documented CORS/frontend env pairing.
- Finalize README, architecture notes, cost/scaling notes, and Loom script.
- Run clean-clone demo rehearsal before recording.

### Acceptance Criteria

- Clean clone can install, configure env, and run.
- Mocked tests pass without paid providers.
- CI runs backend lint, backend tests, frontend lint, frontend typecheck, frontend build, markdown lint, and mocked smoke tests.
- Backend can be built from `backend/Dockerfile` for Render and binds to the Render `PORT` value.
- Hosted frontend/backend deployments can be connected with `NEXT_PUBLIC_API_BASE` and `CORS_ORIGINS` without CORS errors.
- Loom script explains cost, scaling, quality tradeoffs, and fallback paths.
- Final demo has no known blocking bugs.
