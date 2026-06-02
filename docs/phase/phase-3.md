# Phase 3 — Product UI

## Scope

Phase 3 makes the demo experience clearer, faster to understand, and easier to present.

Included in this phase:

- Improve side-by-side video cards with clearer metrics and unavailable states.
- Add citation chips that clearly map to metadata or transcript chunks.
- Add suggested questions for the assignment prompts.
- Improve loading, progress, empty, and failure states.
- Make the happy-path demo obvious without reading instructions.
- Tighten responsive layout for laptop and recording viewports.
- Add inline URL/platform validation that appears after field interaction or submit.
- Preserve failed inputs for whole-session retry and preserve completed results while editing a new comparison.
- Show duplicate URL warnings without blocking same-video tests.
- Render sanitized session and per-video errors from structured backend error objects.
- Guard UI operations so stale ingest, status, reset, or chat responses cannot overwrite the active view.

Out of scope for this phase:

- Changing the core RAG architecture.
- Adding auth.
- Adding production analytics or monitoring.

## Frontend Validation And Retry UX

The UI validates each URL against the selected platform before `POST /ingest`. YouTube accepts watch, Shorts, and `youtu.be` forms; Instagram accepts Reel URLs only. Pasted values are trimmed before submit, query strings remain valid, both slots may use the same platform, and duplicate URLs show a warning without blocking.

Failed ingestion leaves the current inputs editable. Retry is a whole-session retry: the next successful submit creates a new backend session from the current validated inputs and uses normal extraction-cache behavior. Completed results stay visible while inputs are edited; the UI marks that chat remains tied to the completed session until a new ingest is accepted.

## Operation State

The frontend tracks idle, submitting, processing, completed, failed, offline, and chatting phases. Inputs are locked during submit and processing. Starting a new ingest is blocked while chat streams. Active request/session guards prevent late responses from older status polls, ingest attempts, resets, or chat streams from mutating the current UI.

Reset during processing is labeled as a local reset and uses browser confirmation text that says backend work may continue. Reset during chat streaming aborts the current fetch and clears the draft.

## Failure Rendering

The page renders structured `error.message` values when available and logs structured plus raw error context to the browser console. Per-video cards use `video_error.message` when available, falling back to legacy `video_error_message` only for compatibility.
