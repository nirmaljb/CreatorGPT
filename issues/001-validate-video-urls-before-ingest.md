## Parent PRD

`issues/prd.md`

## What to build

Add end-to-end URL/platform validation before ingestion starts. The slice should reject avoidable bad inputs in the UI and at the API boundary, while still allowing supported YouTube URL forms, Instagram Reel URLs, query strings, trimmed pasted URLs, duplicate URL warnings, and same-platform comparisons as described in the PRD.

## Acceptance criteria

- [ ] Frontend validates each URL against its selected platform before calling ingest.
- [ ] Frontend shows inline validation errors only after field interaction or submit.
- [ ] Frontend disables submit while either URL is invalid.
- [ ] Frontend warns, but does not block, when Video A and Video B use the same URL.
- [ ] YouTube validation accepts common YouTube watch, short, and short-domain URL forms.
- [ ] Instagram validation accepts Instagram Reel URLs only.
- [ ] Query strings and leading/trailing spaces are handled safely.
- [ ] Backend rejects platform/URL mismatches with a structured `422` response.
- [ ] Backend validation runs before session creation, ingest slot acquisition, or rate-limit accounting.
- [ ] Focused backend tests cover accepted URLs, rejected mismatches, non-Reel Instagram URLs, and validation-before-side-effects behavior.
- [ ] Frontend lint, typecheck, and build remain green.

## Blocked by

None - can start immediately

## User stories addressed

- User story 1
- User story 2
- User story 3
- User story 4
- User story 5
- User story 6
- User story 7
- User story 8
- User story 9
- User story 10
- User story 11
- User story 48
- User story 49
- User story 52
- User story 53
- User story 56
- User story 57
