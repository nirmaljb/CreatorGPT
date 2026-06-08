# Progress

## Current Phase

Pivot planning and documentation reset.

## Current Status

- The project has pivoted from the old YouTube/Instagram comparison RAG demo to an OAuth-connected YouTube performance diagnosis product.
- The active branch is `postmortom`.
- The new product is report-first, not chatbot-first.
- The central product object is now planned as `analysis_run`, not `session_id`.
- YouTube OAuth is required for MVP because reliable diagnosis depends on authenticated creator analytics.
- The system must analyze first and ask the user targeted questions only when evidence is insufficient.

## Completed Chunks

- Reached product alignment through design grilling:
  - real pivot on a separate branch;
  - refactor in place while reusing useful infrastructure;
  - OAuth is required for MVP;
  - Google OAuth is the primary login system for MVP;
  - private/testing OAuth access is acceptable for first validation;
  - users select owned channel videos after connecting YouTube;
  - baseline comparisons are channel-relative;
  - evidence gates are required before naming a primary bottleneck;
  - deterministic analytics own diagnosis, while LLMs own explanation and coaching;
  - comments need a bounded Audience Signals Agent;
  - chat is attached to reports and grounded in analysis snapshots.
- Replaced old `AGENTS.md` instructions with pivot-specific workflow, evidence standards, OAuth/privacy rules, analyzer boundaries, schema direction, and source citation expectations.
- Replaced `.codex/PRODUCT_SPEC.md` with the YouTube video performance diagnosis product spec.
- Replaced `.codex/ARCHITECTURE.md` with the OAuth-connected analysis-run architecture.
- Replaced `README.md` with the new project overview, architecture, setup direction, and MVP milestone sequence.
- Replaced `.codex/PLANS.md` with pivot milestones and acceptance criteria.
- Reset this progress file for the new product direction.
- Tightened the MVP product contract through a second design-grilling pass:
  - OAuth-first and owned-video diagnosis wins over public URL diagnosis for MVP;
  - MVP diagnosis is long-form-only, with Shorts detected and excluded;
  - first 7 completed days is the default comparison window, with early-read downgrades;
  - fewer than 5 comparable prior long-form videos prevents confident primary-bottleneck diagnosis;
  - CTR and impressions are optional/manual context, so packaging confidence is capped without click-opportunity evidence;
  - automated thumbnail image analysis is excluded from MVP; thumbnails are stored and displayed but not interpreted without a future cited vision analyzer;
  - retention curve or equivalent manual retention evidence is required for precise hook and pacing diagnosis;
  - comments are bounded supporting evidence and unavailable comments are neutral;
  - engagement/satisfaction uses opportunity-normalized metrics;
  - distribution expansion requires trend, traffic-source, or audience-segment evidence and cannot claim algorithm certainty;
  - reports use compact timestamped evidence cards with embedded YouTube player seek actions, not essay-first output;
  - every factual report claim requires machine-readable citations to stored evidence;
  - strict report JSON/citation validation is required before display, with deterministic fallback if LLM generation fails;
  - manual metrics, manual transcripts, and user context are stored separately and labeled as user-provided;
  - transcript acquisition uses bounded retries, Whisper fallback, and optional user-provided transcript/script;
  - follow-up chat stays grounded in immutable analysis snapshots unless the user explicitly refreshes or adds context;
  - lightweight report feedback is captured against `analysis_run_id` for validation, not used as diagnosis evidence or chat memory;
  - video selection is manual for MVP and the app should not precompute private analytics for every upload to auto-rank underperformers;
  - MVP analysis execution uses FastAPI background tasks with explicit queue-ready statuses instead of adding a durable job queue now;
  - retrying a failed analysis creates a new linked `analysis_run` instead of mutating the failed run;
  - refreshing analytics or adding interpretation-changing manual context also creates linked runs with explicit `run_reason`.
- Updated `AGENTS.md`, `README.md`, `.codex/PRODUCT_SPEC.md`, `.codex/ARCHITECTURE.md`, and `.codex/PLANS.md` with these stricter reliability decisions.
- Added a frontend `/faq` page entry explaining why the product does not compare creators to big channels by default and treats future reference videos as study material rather than copy benchmarks.
- Wrote `issues/prd.md` for the OAuth-connected concierge skeleton:
  - creator Google/YouTube connection;
  - admin-only internal evidence dashboard;
  - first-7-day analytics and baseline package;
  - retention and transcript mapping priority;
  - concierge report workflow;
  - anti-imitation product principles;
  - extensive user stories, implementation decisions, testing decisions, out-of-scope items, and further notes.
- Broke `issues/prd.md` into approved vertical-slice implementation issues:
  - `issues/001-connect-youtube-oauth-and-session-shell.md`;
  - `issues/002-choose-youtube-channel.md`;
  - `issues/003-select-owned-long-form-upload.md`;
  - `issues/004-create-analysis-run-with-honest-progress.md`;
  - `issues/005-admin-run-list-and-access-boundary.md`;
  - `issues/006-capture-selected-video-evidence-snapshot.md`;
  - `issues/007-build-baseline-evidence-package.md`;
  - `issues/008-capture-retention-evidence-and-drop-candidates.md`;
  - `issues/009-acquire-transcript-and-map-retention-moments.md`;
  - `issues/010-add-manual-context-and-linked-revision-runs.md`;
  - `issues/011-admin-notes-usage-ledger-and-scoped-export.md`;
  - `issues/012-concierge-report-workflow-and-validation-template.md`;
  - `issues/013-creator-settings-for-disconnect-and-data-deletion.md`;
  - `issues/014-retire-legacy-comparison-surface-and-enforce-mvp-guardrails.md`.
- Improved the frontend OAuth connection shell for usability and visual polish:
  - added skip-link support and main-content targets across the home and FAQ pages;
  - changed internal navigation to Next `Link`;
  - added async connection status announcement, alert/status roles, clearer OAuth CTA labels, and last-verified display;
  - reshaped the home page into a creator evidence workbench with readiness steps, scoped-access rows, and clearer privacy guardrails;
  - replaced the shared CSS with stronger focus states, responsive fixed-size typography, better long-text wrapping, reduced-motion handling, and a cooler multi-accent palette.
- Fixed the frontend OAuth reconnect entrypoint:
  - changed the connection CTA from a browser-visible `NEXT_PUBLIC_API_BASE` URL to same-origin `/auth/google/start`;
  - added a frontend OAuth start route that asks the backend for the Google authorization redirect and redirects directly to that provider URL when available;
  - added a same-origin `/api/me` route that proxies the backend session payload so the connection shell no longer needs to expose the backend base URL in client code;
  - kept backend API origin resolution server-side with `BACKEND_API_BASE`, `API_BASE`, or the existing `NEXT_PUBLIC_API_BASE` fallback.
- Fixed the OAuth unavailable redirect diagnosis path:
  - backend settings now accept canonical `GOOGLE_OAUTH_CLIENT_ID`, `GOOGLE_OAUTH_CLIENT_SECRET`, and `TOKEN_ENCRYPTION_KEY` plus the legacy `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, and `OAUTH_TOKEN_ENCRYPTION_KEY` aliases;
  - frontend `/auth/google/start` now preserves the backend's sanitized failure reason on the home-page redirect instead of collapsing every failure to bare `auth=unavailable`;
  - the connection shell now displays that OAuth-start reason to the user;
  - README setup now documents the canonical OAuth env names;
  - the OAuth test fixture now shares one in-memory SQLite connection across `TestClient` threads so auth route tests exercise the intended tables.
- Accepted the multi-page SaaS route contract for the frontend:
  - `/` is the public landing page;
  - `/auth` is the focused Google/YouTube sign-in and data-permission page;
  - `/app` is the authenticated workspace for video selection and diagnosis;
  - `/faq` remains a supporting trust and education page;
  - connected users visiting `/auth` should continue to `/app`, while unauthenticated users visiting `/app` should continue to `/auth`.
- Accepted the public landing-page responsibility and product voice:
  - `/` should state the core promise, explain the read-only trust boundary, and drive one primary `Connect YouTube` CTA;
  - the product must not market itself as a clickbait title generator, thumbnail generator, generic AI coach, or way to copy large creators' videos or style;
  - the tone should be direct and useful like an experienced creator friend, not flattering, gimmicky, or performatively "brutally honest";
  - the diagnosis should stay grounded in the creator's own channel, own videos, audience patterns, and evidence limits.

## Current Next Step

Continue the SaaS frontend design grilling, then implement the accepted route split alongside `issues/001-connect-youtube-oauth-and-session-shell.md`.

Implementation must enforce the accepted MVP constraints above while building this skeleton.

## Known Issues

- The codebase still contains legacy YouTube/Instagram two-video comparison concepts.
- Legacy endpoints and tests will need phased removal or migration.
- Alembic is not installed or configured yet.
- OAuth token encryption is not implemented yet.
- YouTube Data API and YouTube Analytics API provider wrappers are not implemented yet.
- Manual evidence storage, report citation validation, and deterministic report fallback are not implemented yet.
- Structured-first manual context fields are not implemented yet.
- Report feedback storage and copied-output tracking are not implemented yet.
- Linked retry for failed analysis runs is not implemented yet.
- Linked refresh and manual-context revision runs are not implemented yet.
- Local `.env` currently lacks Google OAuth client credentials; until `GOOGLE_OAUTH_CLIENT_ID` and `GOOGLE_OAUTH_CLIENT_SECRET` are populated, `/auth/google/start` correctly returns `Google OAuth is not configured`.

## Verification

- Documentation files were rewritten in place.
- No code or tests were changed in this documentation reset chunk.
- `git diff --check` passed.
- A targeted old-product term scan was run against the rewritten docs; remaining references are intentional migration notes.
- Markdown lint could not run because `frontend/node_modules/.bin/markdownlint-cli2` is not present in this checkout.
- Latest documentation tightening chunk verification:
  - `git diff --check` passed.
  - Stale-decision scan found no conflicting baseline or Shorts wording; remaining hits are intentional "not a generic chatbot" and "no uncited LLM prose" rules.
  - Unrelated deleted `issues/` files and untracked `.codex/skills/web-design-guidelines/` were observed in the worktree and left untouched.
  - Linked-run schema was checked after correction; `parent_analysis_run_id` and `run_reason` now live under `analysis_runs`, and `git diff --check` passed.
  - Frontend FAQ page entry was added; markdown FAQ was restored to avoid putting this in `docs/FAQ.md`.
  - Frontend typecheck could not run meaningfully because `frontend/node_modules` is missing; the failure was missing React/JSX type dependencies, not a page-specific type error.
  - New PRD verification:
    - `git diff --check` passed.
    - `issues/prd.md` was written with 283 lines.
    - Markdownlint could not run because `frontend/node_modules/.bin/markdownlint-cli2` is unavailable in this checkout.
  - PRD-to-issues verification:
    - 14 numbered issue files were generated in `issues/`.
    - `git diff --check` passed.
  - Frontend UI usability chunk verification:
    - `npm run typecheck` passed in `frontend`.
    - `npm run lint` passed in `frontend`.
    - `git diff --check` passed.
    - Next dev server started at `http://127.0.0.1:3000` after localhost binding escalation.
    - `curl -I http://127.0.0.1:3000` and `curl -I http://127.0.0.1:3000/faq` returned HTTP 200.
    - Rendered HTML for `/` and `/faq` was fetched and includes the new skip link, main-content targets, revised connection shell, and FAQ content.
    - In-app Browser visual inspection could not run because the listed Browser plugin reported no available `iab` browser instance.
  - OAuth reconnect URL fix verification:
    - `npm run typecheck` passed in `frontend`.
    - `npm run lint` passed in `frontend`.
    - `git diff --check` passed.
    - Next dev server started at `http://127.0.0.1:3100` after localhost binding escalation.
    - Rendered HTML for `/` contains `href="/auth/google/start"` on the connection CTA.
    - `curl http://127.0.0.1:3100/api/me` returned the backend session payload through the frontend proxy.
    - `curl -D - http://127.0.0.1:3100/auth/google/start` returned a frontend-origin fallback redirect in this local environment because backend OAuth start did not return a provider redirect; it did not expose `localhost:8000` as the browser navigation target.
  - OAuth unavailable redirect diagnosis fix verification:
    - backend dev dependencies were installed into `backend/.venv` to run focused auth tests.
    - `backend/.venv/bin/pytest backend/tests/test_auth_oauth.py` passed.
    - `backend/.venv/bin/ruff check backend/app/core/config.py backend/app/auth/crypto.py backend/tests/test_auth_oauth.py` passed.
    - direct backend import checks confirmed the legacy OAuth env aliases populate the canonical settings.
    - `npm run typecheck` passed in `frontend`.
    - `npm run lint` passed in `frontend`.
    - `git diff --check` passed.
    - `curl -D - http://127.0.0.1:3000/auth/google/start` now redirects to `/?auth=unavailable&reason=Google+OAuth+is+not+configured` in this local environment.
