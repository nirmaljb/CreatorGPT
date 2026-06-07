## Parent PRD

`issues/prd.md`

## What to build

Create the first immutable analysis run for a selected owned video and show honest progress states while backend evidence collection is queued and executed. This slice establishes `analysis_run` as the canonical product object and keeps retry history auditable.

## Acceptance criteria

- [ ] Alembic migrations add `analysis_runs` with `queued`, `running`, `needs_input`, `completed`, and `failed` statuses, plus `parent_analysis_run_id`, `run_reason`, selected channel/video references, timestamps, and sanitized failure fields.
- [ ] `POST /analysis-runs` creates a new queued run for the authenticated user's selected channel and selected owned long-form video.
- [ ] FastAPI background tasks move the run through bounded state transitions and can record sanitized provider failures without mutating prior snapshots.
- [ ] `GET /analysis-runs/{id}` returns creator-safe run status, step labels, required action when applicable, and no fake progress percentages.
- [ ] The creator-facing UI submits the selected video for review and shows step labels such as queued, collecting evidence, needs input, evidence collected, or failed.
- [ ] Retrying a failed run creates a new linked run with `run_reason` set to `retry` and does not overwrite the failed run.
- [ ] Server-side authorization prevents users from reading or retrying another user's runs.
- [ ] Tests cover run creation, status transitions, progress response shape, failed-run retry linking, immutability of older runs, sanitized errors, and creator UI state rendering.

## Blocked by

- Blocked by `issues/003-select-owned-long-form-upload.md`

## User stories addressed

- User story 16
- User story 17
- User story 18
- User story 53
- User story 54
