## Parent PRD

`issues/prd.md`

## What to build

Add whole-session retry behavior for failed ingestion and non-destructive editing after completed ingestion. Retry should submit the current inputs as a new session, preserve editable URLs after failure, reuse cache by default, and show when completed-session inputs have been changed for a new comparison.

## Acceptance criteria

- [ ] Failed ingestion keeps the user's current URLs and platform selections editable.
- [ ] Retry creates a new session instead of resuming or modifying the failed session.
- [ ] Retry submits the current validated inputs.
- [ ] Retry uses normal cache behavior and does not add a frontend force-refresh toggle.
- [ ] Completed session results remain visible while the user edits inputs.
- [ ] The UI indicates when edited inputs differ from the completed session's submitted inputs.
- [ ] Starting a new comparison clears the old result only after submit.
- [ ] Chat remains tied to the completed session until a new ingest starts.
- [ ] Progress documentation records the whole-session retry decision.

## Blocked by

- Blocked by `issues/002-add-structured-app-error-contract.md`
- Blocked by `issues/003-surface-friendly-ingestion-failures.md`

## User stories addressed

- User story 12
- User story 13
- User story 14
- User story 35
- User story 36
- User story 37
- User story 58
