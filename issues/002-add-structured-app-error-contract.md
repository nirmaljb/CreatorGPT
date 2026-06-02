## Parent PRD

`issues/prd.md`

## What to build

Add the shared structured application error contract used by validation, ingestion, status, rate-limit, and chat paths. This slice establishes the response envelope, parsing compatibility, and persisted minimal structured error fields without fully remapping every pipeline failure yet.

## Acceptance criteria

- [ ] App-owned API failures can return an error envelope with code, message, scope, retryability, and optional video or field context.
- [ ] Frontend error parsing accepts the new envelope and remains compatible with existing `detail` strings or legacy error text.
- [ ] Session status can expose both the existing session error message and a structured session error object.
- [ ] Video metadata status can expose both the existing video error message and a structured video error object.
- [ ] Minimal structured session error fields are persisted.
- [ ] Minimal structured video error fields are persisted.
- [ ] Existing string error fields remain available for compatibility.
- [ ] Backend tests cover response envelope parsing, status serialization, and persisted structured error fields.

## Blocked by

- Blocked by `issues/001-validate-video-urls-before-ingest.md`

## User stories addressed

- User story 44
- User story 45
- User story 46
- User story 47
- User story 50
- User story 51
- User story 53
- User story 57
