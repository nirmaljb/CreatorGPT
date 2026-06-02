## Parent PRD

`issues/prd.md`

## What to build

Harden frontend status polling so offline, slow, unreachable, stalled, and terminal states are communicated clearly. The frontend should warn without falsely failing sessions; backend status remains the source of truth.

## Acceptance criteria

- [ ] Browser offline state shows a connection warning instead of an ingestion failure.
- [ ] Status polling resumes when the browser reports online again.
- [ ] Slow or unreachable status requests show a connection warning and keep retrying while appropriate.
- [ ] Polling stops when the session reaches failed, completed, or ready status.
- [ ] The frontend shows a non-terminal warning after 60 seconds without movement in current step, progress percent, or updated timestamp.
- [ ] The stalled warning resets when status movement resumes.
- [ ] The frontend does not mark sessions failed based on client-side time alone.
- [ ] Backend stale-session failure remains visible through normal status responses.
- [ ] Frontend lint, typecheck, and build remain green.

## Blocked by

- Blocked by `issues/005-frontend-operation-state-guards.md`

## User stories addressed

- User story 26
- User story 27
- User story 28
- User story 29
- User story 30
- User story 31
- User story 56
- User story 57
