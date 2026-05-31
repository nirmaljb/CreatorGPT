# Progress

## Current Phase

Phase 1 implementation.

## Current Status

- Repository initialized on `main`.
- Planning decisions recorded in `.codex/Agents.md`.
- Backend and frontend Phase 1 implementation files have been added and lightweight checks pass.
- Backend dev server is running at `http://127.0.0.1:8000`.
- Frontend dev server is running at `http://localhost:3001` because port 3000 is already occupied locally.
- Live ingest and chat smoke tests pass after the YouTube transcript fast-path and async ingestion changes.
- Project docs have been moved under `.codex/`.
- Phase documentation is tracked under `docs/phase/`; Phase 1 now includes high-level Mermaid flow diagrams.

## Completed Chunks

- Created implementation plan.
- Locked Phase 1 provider choices: Groq chat and FastEmbed/BGE embeddings.
- Added `.env.example`, `.gitignore`, `README.md`, backend dependencies, package scaffolding, settings, SQLAlchemy models, Postgres helpers, and Qdrant/FastEmbed helpers.
- Added ingestion modules for metadata scraping, audio download, faster-whisper transcription, transcript chunking, and end-to-end ingestion status updates.
- Added LangGraph retrieval flow, prompt construction, Groq streaming client, SSE response service, and FastAPI endpoints for health, ingest, status, messages, and chat.
- Added Next.js app with URL ingestion form, status polling, persisted session reload, side-by-side video metadata panels, chat UI, streaming SSE parsing, and source tags.
- Installed frontend dependencies and generated `frontend/package-lock.json`.
- Installed backend dependencies in `backend/.venv`.
- Fixed Next.js workspace-root warning by setting `outputFileTracingRoot`.
- Adjusted prompt formatting so missing follower counts are exposed as `unavailable` instead of `0`.
- Replaced fixed YouTube/Instagram frontend inputs with two video slots, each with a YouTube/Instagram selector.
- Updated `/ingest` to accept `videos: [{ video_id, platform, url }]` while keeping the old `youtube_url`/`instagram_url` payload compatible.
- Changed long-video handling from hard failure to first-window trimming based on `MAX_VIDEO_SECONDS`.
- Changed ingestion to scrape/store metadata for both videos before starting audio download/transcription.
- Added structured console logging across startup, metadata scraping, audio download, transcription, chunking, Qdrant upsert, retrieval, and failures.
- Added Qdrant collection dimension validation during startup.
- Expanded development CORS defaults to allow local frontend ports 3000 and 3001.
- Added persisted session progress fields: `current_step` and `progress_percent`.
- Updated ingestion to write progress at metadata, download, transcription, chunking, embedding, finished-video, ready, and failure stages.
- Updated frontend status display with a progress bar and adaptive polling delays instead of fixed 2.5-second polling.
- Added `youtube-transcript-api` as a backend dependency.
- Added YouTube video ID extraction and caption fast-path with Whisper fallback.
- Refactored ingestion so per-video transcript/vector work runs concurrently after the metadata pass.
- Added transcript source tags into Qdrant chunk payloads and prompt context.
- Moved default runtime audio outside the repo and redirected legacy `TMP_DIR=tmp` to `/private/tmp/creator-rag`.
- Added Qdrant payload index creation for `session_id`, `video_id`, and `is_hook`.
- Moved root `AGENT.md` to `.codex/Agents.md`.
- Moved root `Progress.md` to `.codex/Progress.md`.
- Added `.codex/PRODUCT_SPEC.md`, `.codex/ARCHITECTURE.md`, and `.codex/PLANS.md`.
- Added the revised Phase 0-4 plan to `.codex/Agents.md` and expanded phase milestones with acceptance criteria in `.codex/PLANS.md`.
- Added scope-only docs for Phase 1 through Phase 4 under `docs/phase/`.
- Updated `.codex/Agents.md` workflow so phase docs start with scope and gain technologies, flow, components, and tradeoffs as each phase progresses.
- Updated `docs/phase/phase-1.md` so the user flow, ingest/status/chat flow, and component flow are represented as high-level Mermaid diagrams instead of ordered flow lists.

## Current Next Step

Use `.codex/PLANS.md` for the next large task, likely Phase 2 grounded intelligence.

## Known Issues

- None currently blocking Phase 1.

## Manual Test Results

- `python3 -m compileall backend/app` passed.
- `ffmpeg -version` passed; ffmpeg 8.1.1 is installed.
- `npm install` passed after network escalation.
- `npm run build` passed for the Next.js frontend.
- `backend/.venv/bin/pip install -r backend/requirements.txt` passed after network escalation.
- `backend/.venv/bin/python -m compileall backend/app` passed.
- `backend/.venv/bin/python -c "import backend.app.main"` passed.
- Chunker smoke test passed for source tags, overlap chunking, and hook flag.
- `npm run dev` initially failed under sandbox port permissions, then started successfully after escalation.
- `backend/.venv/bin/python -c "import backend.app.main"` passed after the latest fixes.
- `npm run build` passed after the latest frontend platform-selector changes.
- `GET /health` on the running backend returned `{"api": true, "postgres": true, "qdrant": true}` using the configured cloud credentials.
- Backend restart after Qdrant dimension validation passed; startup logged existing collection dimension `384` matching expected `384`.
- CORS preflight from `http://localhost:3001` to `POST /ingest` passed.
- `GET /status/{session_id}` now returns `current_step`, `progress_percent`, and `updated_at`.
- `youtube_transcript_api` live smoke test returned 1,280 caption-derived word objects for `https://youtu.be/cLpfcn_dPEo`.
- Live ingest for the two YouTube URLs from the issue completed with status `ready` in about 14 seconds using `youtube_captions` for both videos.
- The same live ingest upserted 38 chunks for Video A and 27 chunks for Video B to Qdrant.
- Chat smoke test streamed an engagement-rate answer with `[Video A metadata]` and `[Video B metadata]` citations.
- Documentation restructure verified by listing `.codex/` contents.
