## Parent PRD

`issues/prd.md`

## What to build

Map ingestion failures into plain-language structured session and video errors. The completed slice should make failed metadata extraction, transcript generation, vector storage, stale ingestion, and unknown provider errors visible to users without exposing raw technical details in the page.

## Acceptance criteria

- [ ] Known metadata extraction failures map to platform-specific access error codes and friendly messages.
- [ ] Instagram access failures mention that the Reel may be private, unavailable, or require cookies.
- [ ] Transcript and transcription failures map to user-facing transcript error codes.
- [ ] Vector store failures map to a user-facing vector store error code.
- [ ] Stale processing sessions retain the backend as the source of truth and expose structured retryable failure state.
- [ ] Unknown pipeline failures are sanitized through a fallback error category.
- [ ] Failed sessions show a session-level blocking error.
- [ ] Failed videos show per-video friendly errors on the relevant video card.
- [ ] Successful video metadata can remain visible when the other video fails.
- [ ] Chat remains blocked unless both videos complete successfully.
- [ ] Backend console logs retain technical details needed for debugging.
- [ ] Frontend logs structured/raw error context to the browser console without rendering raw provider details.
- [ ] Backend tests cover representative stage-owned error mappings and fallback sanitization.

## Blocked by

- Blocked by `issues/002-add-structured-app-error-contract.md`

## User stories addressed

- User story 15
- User story 16
- User story 17
- User story 18
- User story 19
- User story 20
- User story 21
- User story 22
- User story 31
- User story 45
- User story 46
- User story 47
- User story 54
- User story 55
- User story 57
