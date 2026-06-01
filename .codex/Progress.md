# Progress

## Current Phase

Phase 2 implementation.

## Current Status

- Repository initialized on `main`.
- Planning decisions recorded in `.codex/Agents.md`.
- Backend and frontend Phase 1 implementation files have been added and lightweight checks pass.
- Backend dev server is running at `http://127.0.0.1:8000`.
- Fresh backend dev server with the latest ingestion changes is running at `http://127.0.0.1:8001`.
- Frontend dev server is running at `http://localhost:3001` because port 3000 is already occupied locally.
- Live ingest and chat smoke tests pass after the YouTube transcript fast-path and async ingestion changes.
- Project docs have been moved under `.codex/`.
- Phase documentation is tracked under `docs/phase/`; Phase 1 now includes high-level Mermaid flow diagrams.
- Phase 2 router implementation is in progress with explicit route labels, rules-first classification, named retrieval policies, and route-aware assignment evals.

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
- Confirmed a live mixed YouTube + Instagram Reel ingest returns `session_id` immediately, stores both metadata rows, reaches terminal status, and streams a cited chat response.
- Added Postgres-backed extraction cache support keyed by platform, URL, cache version, and `MAX_VIDEO_SECONDS`, with `FORCE_REFRESH=true` to bypass cache reads.
- Added platform-specific extractor classes for YouTube and Instagram so captions/Whisper behavior is explicit per platform.
- Added per-video ingestion diagnostics in Postgres and status responses: `ingest_status`, `video_error_message`, `transcript_source`, `chunk_count`, cache flags, and raw-metadata presence.
- Added raw `yt-dlp` metadata storage on video metadata rows and extraction cache entries.
- Updated the terminal ingest session status to `completed` while keeping `/chat` compatible with older `ready` sessions.
- Fixed compare-query retrieval so questions mentioning both Video A and Video B retrieve transcript chunks from both videos instead of filtering to Video A.
- Added typed Postgres metadata tools for video metrics, creator info, engagement comparison, and session video summaries.
- Added question routing so numeric/creator/metadata questions bypass Qdrant retrieval, semantic transcript questions retrieve from Qdrant, and mixed comparison questions use both metadata tools and Qdrant.
- Changed YouTube caption ingestion so captions are uncapped by `MAX_VIDEO_SECONDS`; videos longer than 10 minutes can ingest when captions are available, while audio/Whisper fallback remains capped.
- Bumped extraction cache version for transcript provider changes so older capped-caption cache entries are not reused.
- Replaced local `faster-whisper` transcription with Groq `whisper-large-v3` transcription and removed the local dependency/config.
- Bumped extraction cache version to `extract-v3` so older local-Whisper transcript cache entries are not reused.
- Added `scripts/eval_assignment_questions.py`, a small assignment eval runner that asks the five required demo questions against a completed session through the streaming `/chat` API.
- Added reusable eval logic in `backend.evals.assignment_eval` for later mocked CI coverage.
- Added eval validation for streaming success, non-empty cited answers, source routing, Postgres-backed numeric values, unavailable missing follower counts, early hook chunks, and mixed comparison transcript evidence from both videos.
- Tightened Video A/B routing detection so "Suggest improvements for B based on what worked in A" is treated as a mixed comparison and retrieves chunks for both videos.
- Documented the assignment eval command in `README.md` and `docs/phase/phase-2.md`, and recorded the eval-first workflow in `AGENTS.md` and `.codex/PLANS.md`.
- Added a root `Makefile` with CI-equivalent targets for backend lint/tests, frontend lint/typecheck/build, markdown lint, and a mocked smoke test.
- Added backend dev tooling config: `backend/requirements-dev.txt`, `pyproject.toml` for Pytest/Ruff, and `.pre-commit-config.yaml` local hooks.
- Added frontend ESLint and markdown lint dependencies/config, plus `lint`, `typecheck`, and `lint:md` scripts.
- Added `.github/workflows/ci.yml` and `.github/pull_request_template.md` so required CI is provider-mocked and does not require Groq, Qdrant Cloud, Neon, YouTube, or Instagram.
- Added `backend/tests/test_mocked_smoke.py` to patch API dependencies and verify ingest -> status -> streamed chat without external providers.
- Reworked `README.md` into a cleaner project entry point with a demo placeholder, documentation map, technology table, high-level pipeline, installation guide, checks, and eval commands.
- Changed the README high-level pipeline from an ordered list to a Mermaid flowchart.
- Fixed the README Mermaid diagram by quoting labels that contain braces and HTML line breaks so GitHub can render it.
- Fixed the assignment eval failure where the "why did A get more engagement" answer could use retrieved chunks as hidden context but cite only metadata.
- Added mixed-route prompt requirements so comparison answers cite transcript chunks when chunks are retrieved.
- Added metric availability flags derived from raw metadata so missing Instagram views, engagement rates, and follower counts are shown as `unavailable` instead of being treated as real zeroes.
- Updated metadata tools, prompt context, eval validation, and frontend metric cards to respect unavailable extractor counts.
- Updated engagement comparison metadata so a missing view denominator marks the comparison incomplete instead of declaring Video A the winner.
- Tightened eval validation so unavailable Video B views or engagement cannot pass as `0 views` or `0%`.
- Tightened citation formatting so prompts and evals require exact source tags instead of wrapper citations like `[source_tag: [Video A metadata]]` or fake tags like `[POSTGRES METADATA TOOL RESULTS]`.
- Added a Phase 1 stale-ingest guard: `/status/{session_id}` marks old `processing` sessions as `failed` after `INGEST_STALE_SECONDS` and marks non-terminal video rows failed.
- Changed the frontend refresh behavior so it clears the old localStorage session key and starts from a clean UI state instead of restoring a previous stuck session.
- Added frontend offline/API-unreachable handling so status polling pauses with a connection message and resumes loading when the browser reports it is online again.
- Documented the no-retry Phase 1 tradeoff and future explicit retry direction in `AGENTS.md`, `.codex/ARCHITECTURE.md`, `.codex/PLANS.md`, and `docs/phase/phase-1.md`.
- Corrected the `AGENTS.md` operating workflow to point future agents at the existing root `AGENTS.md` file plus `.codex/Progress.md`.
- Added the Phase 2 rules-first LangGraph router with explicit `METADATA_ONLY`, `TRANSCRIPT_ONLY`, `HOOK_COMPARISON`, `MIXED_COMPARISON`, `IMPROVEMENT_SUGGESTION`, and `FOLLOW_UP` routes.
- Changed the RAG graph from a mostly linear flow to conditional routing: metadata-only paths end after typed Postgres tools, hook paths retrieve `is_hook=true` chunks, and mixed/improvement paths combine metadata tools with transcript retrieval.
- Added minimal follow-up resolution for obvious video references such as "their", "that video", and "what about B", then re-route the resolved question.
- Updated route-specific prompt requirements for hook, mixed, improvement, transcript, and metadata-only answers.
- Updated Phase 2 documentation, architecture notes, milestone notes, and agent decisions with the rules-first router tradeoff.
- Added named Phase 2 retrieval policies for hook, Video A, Video B, balanced comparison, and metadata-augmented retrieval.
- Changed comparison, hook, mixed, and improvement retrieval to avoid one global vector search and instead retrieve balanced Video A and Video B context.
- Exposed `route` and `retrieval_policy` in `/chat` SSE `sources` and `done` events for route-aware eval validation.
- Tightened assignment eval cases to assert expected routes, expected retrieval policies, hook-only answer citations, exact metadata citations, and A/B transcript chunk citations for mixed and improvement answers.
- Changed backend startup so Qdrant collection validation is non-fatal by default; the API boots in degraded mode with `/health` showing `qdrant: false`, while ingest/chat still fail visibly if Qdrant is required and unreachable.
- Added `REQUIRE_QDRANT_ON_STARTUP` for fail-fast deployments and `QDRANT_CHECK_COMPATIBILITY=false` to suppress Qdrant server-version probe warnings by default.

## Current Next Step

Run `python scripts/eval_assignment_questions.py --session-id <id>` against a completed YouTube + Instagram session when the local backend and Qdrant Cloud are reachable before making further retrieval, chunking, embedding, or routing optimizations.

## Known Issues

- None currently blocking Phase 2.

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
- `backend/.venv/bin/python -m compileall backend/app backend/tests` passed after ingestion cache/extractor changes.
- `backend/.venv/bin/python -m unittest discover backend/tests` passed for cache key/sessionization behavior and compare-query routing.
- `backend/.venv/bin/python -m unittest discover backend/tests` passed after metadata-tool routing was added; tests assert numeric metadata questions do not call Qdrant retrieval.
- `backend/.venv/bin/python -m unittest discover backend/tests` passed after uncapping YouTube captions; tests assert caption words beyond 10 minutes are kept and long captioned YouTube videos do not use Whisper.
- `backend/.venv/bin/python -m compileall backend/app backend/tests` and `git diff --check` passed after the long-caption change.
- `backend/.venv/bin/python -m unittest discover backend/tests` passed after replacing local transcription with Groq `whisper-large-v3`; tests assert the Groq transcription call requests `verbose_json` word timestamps.
- `backend/.venv/bin/python -c "import backend.app.main; import backend.app.ingest.transcriber"` passed after removing the local `faster-whisper` dependency.
- `backend/.venv/bin/pip uninstall -y faster-whisper` removed the local transcription package from the current virtualenv; `pip show faster-whisper` confirms it is no longer installed.
- `npm run build` passed after adding per-video diagnostics and `completed` status support to the frontend.
- Live mixed ingest on port 8001 with YouTube `https://youtu.be/cLpfcn_dPEo` and Instagram `https://instagram.com/reel/DEDbGqpyfkT/` returned `session_id=994ea123-443d-4dc9-80a0-2aac7e8627ae` immediately and reached `completed`.
- That live mixed ingest stored raw metadata for both rows, used `captions` for Video A, used `whisper` for Video B, and upserted 27 Video A chunks plus 3 Video B chunks.
- Chat smoke tests on the completed session streamed cited answers; a Video B query retrieved `[Video B, chunk 0]`, `[Video B, chunk 1]`, and `[Video B, chunk 2]`.
- Repeat ingest `session_id=4920d31a-0ee2-4d00-8b5b-e61d3e7a470c` hit the extraction cache for both metadata and transcripts, then completed with cache flags set for both videos.
- Negative ingest `session_id=67fb27f9-9c42-4733-8f47-5f0fc2a48b7b` with a bad Instagram URL failed visibly; `/status` reported Video B `ingest_status=failed`, `transcript_source=unavailable`, and the extractor error message.
- After the compare-query routing fix, chat on cached session `4920d31a-0ee2-4d00-8b5b-e61d3e7a470c` returned source events containing both Video A and Video B transcript chunks.
- Numeric chat smoke test on cached session `4920d31a-0ee2-4d00-8b5b-e61d3e7a470c` for engagement rates returned only metadata sources and produced no Qdrant retrieval log.
- Semantic chat smoke test on the same session for "What does Video B discuss?" retrieved 3 Video B chunks from Qdrant and streamed transcript citations.
- `backend/.venv/bin/python -m compileall backend/app backend/evals backend/tests scripts` passed after adding the assignment eval runner.
- `backend/.venv/bin/python -m unittest backend.tests.test_assignment_eval backend.tests.test_rag_graph` passed; 14 tests covered eval validation and A/B routing.
- `backend/.venv/bin/python -m unittest discover backend/tests` passed; 26 tests total.
- `backend/.venv/bin/python scripts/eval_assignment_questions.py --help` passed.
- `git diff --check` passed after the eval changes.
- `backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt` passed after network escalation to install `pytest`, `ruff`, and `pre-commit`.
- `npm install` in `frontend/` passed after network escalation and updated `frontend/package-lock.json` for ESLint and markdown lint dependencies.
- `npm ci` in `frontend/` passed after the lockfile update.
- `make backend-lint` passed with Ruff check and Ruff format check.
- `make backend-tests` passed with 26 provider-mocked/unit tests selected and 1 smoke test deselected.
- `make mocked-smoke` passed; the smoke test patches FastAPI dependencies and does not call real providers.
- `make frontend-lint`, `make frontend-typecheck`, `make frontend-build`, and `make markdown-lint` passed.
- `make ci` passed end to end.
- `PRE_COMMIT_HOME=/private/tmp/creator-rag-pre-commit backend/.venv/bin/pre-commit run --all-files` passed. The explicit cache path avoids sandbox writes to `~/.cache/pre-commit`.
- `make markdown-lint` passed after the README refresh.
- `make markdown-lint` passed after changing the README high-level pipeline to Mermaid.
- `make markdown-lint` passed after fixing the README Mermaid label syntax.
- `backend/.venv/bin/python -m pytest backend/tests/test_prompt.py backend/tests/test_metadata_tools.py backend/tests/test_assignment_eval.py` passed after the mixed-citation and unavailable-metric fixes.
- `make ci` passed after the mixed-citation and unavailable-metric fixes; backend tests now report 30 selected tests plus the mocked smoke test.
- `backend/.venv/bin/python -m pytest backend/tests/test_metadata_tools.py backend/tests/test_assignment_eval.py backend/tests/test_prompt.py` passed after marking engagement comparisons incomplete when views are unavailable.
- `make ci` passed after the incomplete-engagement comparison fix; backend tests now report 31 selected tests plus the mocked smoke test.
- `backend/.venv/bin/python -m pytest backend/tests/test_prompt.py backend/tests/test_assignment_eval.py` passed after tightening citation formatting.
- `make ci` passed after tightening citation formatting; backend tests now report 33 selected tests plus the mocked smoke test.
- `backend/.venv/bin/python -m pytest backend/tests/test_stale_ingest.py backend/tests/test_status_endpoint.py` passed after adding stale-session detection and status-route coverage.
- `make ci` passed after the stale-session, clean-refresh, and frontend network handling changes; backend tests now report 37 selected tests plus the mocked smoke test.
- `git diff --check` passed after the stale-session and clean-refresh changes.
- `make frontend-lint` and `make frontend-typecheck` passed after adding frontend network console logging.
- `make markdown-lint` and `git diff --check` passed after the latest docs updates.
- Frontend dev server started at `http://localhost:3001`; an escalated `curl -I http://localhost:3001` returned HTTP 200.
- `backend/.venv/bin/python -m pytest backend/tests/test_rag_graph.py backend/tests/test_prompt.py` passed after the explicit Phase 2 route implementation.
- `make ci` passed after the Phase 2 rules-first router implementation; backend tests now report 44 selected tests plus the mocked smoke test.
- `git diff --check` passed after the Phase 2 router implementation.
- A classifier smoke check mapped the five assignment questions to `METADATA_ONLY`, `METADATA_ONLY`, `HOOK_COMPARISON`, `MIXED_COMPARISON`, and `IMPROVEMENT_SUGGESTION`.
- `backend/.venv/bin/python scripts/eval_assignment_questions.py --api-base http://127.0.0.1:8000 --session-id 4920d31a-0ee2-4d00-8b5b-e61d3e7a470c` passed all five live assignment eval questions after the Phase 2 router implementation.
- `backend/.venv/bin/python -m pytest backend/tests/test_rag_graph.py` passed after adding named retrieval policies and balanced A/B comparison retrieval.
- `make backend-lint` and `make backend-tests` passed after adding named retrieval policies; backend tests now report 46 selected tests plus 1 deselected smoke test.
- `make ci` passed after adding named retrieval policies and the markdown final-newline fix for `.codex/skills/grill-me/SKILL.md`.
- `git diff --check` passed after adding named retrieval policies.
- Live assignment eval rerun was attempted after the retrieval-policy change, but the existing backend on port 8000 timed out and a fresh backend on port 8002 could not resolve the configured Qdrant Cloud host from this environment.
- `backend/.venv/bin/python -m pytest backend/tests/test_assignment_eval.py backend/tests/test_rag_service.py` passed after adding route-aware eval checks and chat stream route traces.
- `make backend-lint` and `make backend-tests` passed after the route-aware eval change; backend tests now report 52 selected tests plus 1 deselected smoke test.
- `make ci` passed after the route-aware eval change.
- `git diff --check` passed after the route-aware eval change.
- `backend/.venv/bin/python -m pytest backend/tests/test_startup.py` passed after making Qdrant startup validation non-fatal by default.
- `backend/.venv/bin/python -m pytest backend/tests/test_mocked_smoke.py` passed after making Qdrant startup validation non-fatal by default.
- `make backend-lint` and `make backend-tests` passed after making Qdrant startup validation non-fatal by default; backend tests now report 54 selected tests plus 1 deselected smoke test.
- `backend/.venv/bin/uvicorn backend.app.main:app --host 127.0.0.1 --port 8003` started successfully after the Qdrant startup change and no longer emitted the Qdrant compatibility warning; the temporary process was stopped after verification.
- `make ci` passed after making Qdrant startup validation non-fatal by default.
