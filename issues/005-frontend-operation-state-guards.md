## Parent PRD

`issues/prd.md`

## What to build

Introduce a lightweight frontend operation state model and stale-response guards so only the active ingest, status poll, reset, or chat operation can mutate the current UI. This slice should remove race-prone behavior without adding backend cancellation.

## Acceptance criteria

- [ ] Frontend tracks clear operation phases for idle, submitting, processing, completed, failed, offline, and chatting behavior.
- [ ] Inputs and platform selectors are locked during submit and processing.
- [ ] Ingest submit is guarded in code as well as by disabled UI.
- [ ] Starting a new ingest is blocked while chat is streaming.
- [ ] Late responses from older requests cannot overwrite the current session or messages.
- [ ] Reset during processing is labeled as a local reset, not cancellation.
- [ ] Reset during processing shows a confirmation that backend work may continue.
- [ ] Local reset clears the frontend session state and stops polling the old session.
- [ ] Reset during chat streaming aborts the current stream and clears the draft.
- [ ] Frontend lint, typecheck, and build remain green.

## Blocked by

- Blocked by `issues/004-whole-session-retry-and-input-preservation.md`

## User stories addressed

- User story 32
- User story 33
- User story 34
- User story 35
- User story 36
- User story 37
- User story 38
- User story 39
- User story 40
- User story 56
