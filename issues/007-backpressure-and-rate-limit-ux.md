## Parent PRD

`issues/prd.md`

## What to build

Convert backend backpressure and rate-limit responses into structured, user-facing errors and make the frontend render them clearly. Retry countdown behavior should appear only when the backend provides retry timing.

## Acceptance criteria

- [ ] Concurrent ingestion limit failures return a structured retryable busy error.
- [ ] Per-IP hourly rate-limit failures return a structured retryable error and preserve `Retry-After`.
- [ ] Frontend displays busy/rate-limit errors in plain language.
- [ ] Frontend shows an approximate retry countdown only when `Retry-After` exists.
- [ ] Retry remains disabled until a rate-limit countdown ends.
- [ ] Frontend remains compatible with older `429` text responses.
- [ ] Backend tests cover structured `429` envelopes and retry timing.
- [ ] Frontend lint, typecheck, and build remain green.

## Blocked by

- Blocked by `issues/002-add-structured-app-error-contract.md`

## User stories addressed

- User story 23
- User story 24
- User story 25
- User story 50
- User story 51
- User story 56
- User story 57
