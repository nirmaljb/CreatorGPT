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
- Store vectors in Qdrant with `video_id` and `session_id` payload filters.
- Build minimal Next.js UI with two URL inputs, progress state, and streaming chat.
- Verify one full flow: ingest -> status complete -> chat -> cited answer.

### Acceptance Criteria

- User can ingest two videos from the UI.
- Status reaches `completed` or a readable `failed` state.
- Metadata cards render for both videos when available.
- Per-video status explains platform/caption/download/transcription failures.
- Chat streams and cites metadata/chunks.
- Full flow works against live Neon, Qdrant, and Groq credentials.

## Phase 2 — Grounded Intelligence

### Milestones

- Add LangGraph routing for numeric, semantic, hook, and recommendation questions.
- Use typed Postgres metadata tools for numeric and creator/follower questions.
- Use transcript retrieval only for semantic and recommendation questions.
- Restrict hook comparison to first-5-second chunks.
- Add citation validation.
- Add an eval script for the assignment's expected question set.

### Acceptance Criteria

- Metadata questions do not depend on vector retrieval.
- Numeric and creator questions bypass Qdrant retrieval entirely.
- Hook questions cite hook chunks only.
- Recommendation answers cite transcript evidence and metrics.
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
- Add markdown linting and CI.
- Finalize README, architecture notes, cost/scaling notes, and Loom script.
- Run clean-clone demo rehearsal before recording.

### Acceptance Criteria

- Clean clone can install, configure env, and run.
- Mocked tests pass without paid providers.
- Loom script explains cost, scaling, quality tradeoffs, and fallback paths.
- Final demo has no known blocking bugs.
