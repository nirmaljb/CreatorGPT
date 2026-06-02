# Phase 4 — Resilience and Demo Readiness

## Scope

Phase 4 hardens the project for final review, clean setup, and Loom recording.

Included in this phase:

- Add provider-mocked smoke tests.
- Add root Makefile targets for local and CI checks.
- Add pre-commit, Ruff, Pytest, frontend lint/typecheck/build checks, markdown linting, PR template, and GitHub Actions CI.
- Keep required CI independent of real Groq, Qdrant Cloud, Neon, YouTube, and Instagram credentials.
- Finalize README instructions.
- Finalize architecture notes.
- Add backend Docker deployment support for Render.
- Add cost and scaling notes for 1000 creators per day.
- Write the Loom demo script.
- Run a clean-clone demo rehearsal before recording.
- Return structured user-facing errors for validation, backpressure, rate limits, ingestion, stale sessions, and chat streams.
- Keep status polling resilient to offline, slow, unreachable, stalled, and terminal states without client-side fake failure.
- Keep reset behavior local until backend cancellation or durable queues exist.

Out of scope for this phase:

- Building new product features unrelated to the assignment checklist.
- Full production deployment automation.
- Multi-tenant auth unless explicitly required before submission.

## Current CI Flow

`make ci` runs the required local and GitHub Actions checks:

- `make backend-lint`
- `make backend-tests`
- `make frontend-lint`
- `make frontend-typecheck`
- `make frontend-build`
- `make markdown-lint`
- `make mocked-smoke`

The mocked smoke test patches API dependencies and verifies ingest, status, and streamed chat behavior without calling Groq, Qdrant Cloud, Neon, YouTube, or Instagram.

## Render Backend Deployment

The backend deploy path now uses `backend/Dockerfile` with Render Docker settings:

- Dockerfile path: `./backend/Dockerfile`
- Docker context: `.`
- Command: use the Dockerfile `CMD`
- Health check path: `/health`

The container installs `ffmpeg`, sets `TMP_DIR=/tmp/creator-rag`, and starts Uvicorn on `0.0.0.0:${PORT:-10000}`. `render.yaml` provides a Blueprint-friendly service definition while keeping secrets and provider URLs manual.

The hosted frontend must set `NEXT_PUBLIC_API_BASE` to the backend URL. The backend must set `CORS_ORIGINS` to the deployed frontend origin. `CORS_ORIGIN_REGEX` is available for trusted preview domains, but exact origins are preferred for the final demo.

## Structured Error Safeguards

App-owned failures can return a top-level `error` envelope with `code`, `message`, `scope`, `retryable`, and optional field, video, or retry timing context. Responses keep legacy `detail` text where practical so older parsing paths continue to work during migration.

Session status exposes both `error_message` and structured `error`. Video metadata exposes both `video_error_message` and structured `video_error`. The frontend renders sanitized structured messages and logs structured/raw context to the browser console for debugging.

Ingestion failure mapping is stage-owned first: metadata access failures, transcript/transcription failures, vector-store failures, stale processing, and unknown failures map to stable user-facing categories. Instagram access errors mention private, unavailable, or cookie-required Reels. Raw provider details remain in backend logs and compatibility fields.

## No-Hang Behavior

Status polling stops on terminal `failed`, `completed`, or legacy `ready` statuses. Browser offline state and slow/unreachable status requests show non-terminal connection warnings and continue retrying while appropriate. A 60-second lack of movement in backend `current_step`, `progress_percent`, or `updated_at` shows an informational stalled warning; the frontend does not mark sessions failed based on client time alone.

Chat stream failures use structured SSE `error` events. The frontend replaces empty assistant drafts with friendly failure messages, keeps the original user question visible, and unlocks chat input after the failed stream ends.
