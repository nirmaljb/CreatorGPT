## Parent PRD

`issues/prd.md`

## What to build

Finish the cross-phase error-handling work by updating the project decision records and running the agreed verification pass. This slice should make the retry, structured error, state guard, and no-cancellation decisions visible to future contributors.

## Acceptance criteria

- [ ] Agent decisions and tradeoffs are updated for structured errors, whole-session retry, and local reset behavior.
- [ ] Phase 3 documentation describes the frontend validation, retry, and failure-state UX.
- [ ] Phase 4 documentation describes the resilience, structured error, and no-hang safeguards.
- [ ] Planning documentation reflects the completed cross-phase patch.
- [ ] Progress documentation records what changed, what was verified, and what remains.
- [ ] Focused backend tests pass.
- [ ] Frontend lint passes.
- [ ] Frontend typecheck passes.
- [ ] Frontend build passes.
- [ ] Markdown lint is run or any unrelated known lint blockers are documented.
- [ ] No parent PRD content is modified while creating or completing this issue.

## Blocked by

- Blocked by `issues/001-validate-video-urls-before-ingest.md`
- Blocked by `issues/002-add-structured-app-error-contract.md`
- Blocked by `issues/003-surface-friendly-ingestion-failures.md`
- Blocked by `issues/004-whole-session-retry-and-input-preservation.md`
- Blocked by `issues/005-frontend-operation-state-guards.md`
- Blocked by `issues/006-resilient-status-polling-and-stall-warnings.md`
- Blocked by `issues/007-backpressure-and-rate-limit-ux.md`
- Blocked by `issues/008-structured-chat-stream-errors.md`

## User stories addressed

- User story 56
- User story 57
- User story 58
