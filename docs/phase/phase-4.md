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
