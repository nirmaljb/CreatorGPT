# Architecture

## Stack

- Frontend: Next.js, React, TypeScript.
- Backend: FastAPI.
- Orchestration: LangGraph.
- LLM: Groq `llama-3.3-70b-versatile` for Phase 1 testing.
- Embeddings: FastEmbed `BAAI/bge-small-en-v1.5`.
- Vector DB: Qdrant Cloud.
- Relational DB: Neon Postgres.
- Extraction: `yt-dlp`, `youtube-transcript-api`, Groq `whisper-large-v3`.

## Runtime Flow

1. `POST /ingest` validates two video inputs and creates a Postgres session.
2. Ingestion runs in a FastAPI background task.
3. Metadata for both videos is loaded from the extraction cache or scraped through the platform extractor, then stored first.
4. Per-video transcript/vector work runs concurrently.
5. YouTube tries uncapped captions first, so videos longer than `MAX_VIDEO_SECONDS` can ingest when captions are available.
6. Unavailable YouTube captions fall back to audio download plus Groq `whisper-large-v3`, where audio is trimmed to `MAX_VIDEO_SECONDS`.
7. Instagram uses audio download plus Groq `whisper-large-v3`.
8. Real extractor output is cached in Postgres unless `FORCE_REFRESH=true` bypasses cache reads for the run.
9. Transcript chunks are embedded and stored in Qdrant with payload filters.
10. Completed sessions move to `completed`; failed videos include per-video error details in status responses.
11. Stale `processing` sessions are marked `failed` from the status path after `INGEST_STALE_SECONDS`.
12. The frontend does not restore a saved session on refresh; every page load starts with a clean UI state.
13. `POST /chat` loads chat history and classifies the question with a rules-first LangGraph router.
14. Follow-up questions resolve simple video references from chat history before being re-routed.
15. Metadata questions use typed Postgres metadata tools only and do not query Qdrant.
16. Semantic transcript questions retrieve transcript chunks from Qdrant.
17. Hook comparison questions retrieve Qdrant chunks with `is_hook=true`.
18. Mixed comparison and improvement questions use typed Postgres metadata tools plus Qdrant transcript retrieval.
19. The backend streams a Groq answer with metadata and/or transcript citations. Compare questions that mention both videos retrieve chunks from each video.

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
- `raw_metadata`
- `ingest_status`
- `video_error_message`
- `transcript_source`
- `chunk_count`
- `cache_key`
- `metadata_cached`
- `transcript_cached`

Status responses derive metric availability flags from `raw_metadata` so missing extractor fields can be shown as unavailable without changing the stored integer columns. Engagement-rate comparisons are marked incomplete when any video's view count is unavailable.

### `extraction_cache`

- `cache_key`
- `platform`
- `url`
- `raw_metadata`
- `normalized_metadata`
- `transcript_words`
- `transcript_source`
- `error_message`
- `created_at`
- `updated_at`

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
- `GET /status/{session_id}`: returns status, progress, errors, and metadata. If a `processing` session has not updated within `INGEST_STALE_SECONDS`, this endpoint marks it `failed`.
- `GET /messages/{session_id}`: returns persisted chat history.
- `POST /chat`: streams SSE events for sources, tokens, done, or errors. Accepts `completed` sessions and older `ready` sessions. `sources` and `done` events include `route` and `retrieval_policy` for route-aware evals.

## Chat Routing

- `get_video_metrics(session_id)`: Postgres metadata tool for views, likes, comments, duration, and engagement rate.
- `get_creator_info(session_id, video_id)`: Postgres metadata tool for creator and follower count.
- `get_engagement_comparison(session_id)`: Postgres metadata tool for engagement-rate comparison.
- `get_session_video_summary(session_id)`: Postgres metadata tool for broad metadata summaries.
- The router uses deterministic internal route labels: `METADATA_ONLY`, `TRANSCRIPT_ONLY`, `HOOK_COMPARISON`, `MIXED_COMPARISON`, `IMPROVEMENT_SUGGESTION`, and `FOLLOW_UP`.
- `METADATA_ONLY` bypasses Qdrant entirely.
- `TRANSCRIPT_ONLY` uses Qdrant transcript retrieval.
- `HOOK_COMPARISON` uses Qdrant retrieval with the `is_hook=true` payload filter.
- Named retrieval policies are used instead of one global `top_k` search: `hook_retrieval`, `video_a_retrieval`, `video_b_retrieval`, `comparison_retrieval`, and `metadata_augmented_retrieval`.
- `MIXED_COMPARISON` combines metadata tool results with balanced Qdrant chunks and requires transcript chunk citations when chunks were retrieved.
- `IMPROVEMENT_SUGGESTION` retrieves `top_k=4` Video A evidence for what worked and `top_k=4` Video B evidence for improvement opportunities.
- `comparison_retrieval` retrieves `top_k=4` from Video A and `top_k=4` from Video B, then merges the context.
- `FOLLOW_UP` resolves obvious references such as "their", "that video", and "what about B" from recent chat history, then re-routes.
- Answers must cite exact source tags only, such as `[Video A metadata]` or `[Video B, chunk 0, 00:00-00:16]`.
- Assignment evals assert the expected route and retrieval policy for each required and extended adversarial question, not only that an answer streamed.

## Quality Gates

- `make ci` is the local equivalent of required GitHub Actions checks.
- Required CI runs backend Ruff lint, backend Pytest tests, frontend ESLint, frontend TypeScript typecheck, frontend build, markdown lint, and a provider-mocked smoke test.
- Required CI must not call real Groq, Qdrant Cloud, Neon, YouTube, or Instagram providers. Real-provider checks belong in manual demo runs or a later nightly workflow.

## Auth

No auth in Phase 1. This is a single-user assignment demo. Production would add tenant/user auth before exposing stored sessions.

## Deployment Notes

- Backend needs `GROQ_API_KEY`, `DATABASE_URL`, `QDRANT_URL`, and `QDRANT_API_KEY` for full ingest/chat behavior.
- Qdrant startup validation is non-fatal by default. If Qdrant is unreachable, the API process still starts and `/health` returns `qdrant: false`; ingestion and transcript retrieval still require Qdrant and fail visibly.
- Set `REQUIRE_QDRANT_ON_STARTUP=true` when deployment should fail fast if Qdrant cannot be validated.
- `QDRANT_CHECK_COMPATIBILITY=false` by default suppresses Qdrant server-version probe warnings; collection existence, dimensions, and payload indexes are still checked when Qdrant is reachable.
- `FORCE_REFRESH=true` bypasses extraction-cache reads when a demo needs fresh platform data.
- `ffmpeg` is required for `yt-dlp` audio extraction before Groq Whisper transcription.
- Runtime audio is written outside the repo by default to avoid reload loops.
- For dev reload, use `uvicorn backend.app.main:app --reload --reload-dir backend/app`.
