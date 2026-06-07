## Parent PRD

`issues/prd.md`

## What to build

Replace the legacy public comparison/chatbot surface with the concierge skeleton guardrails. The active product should be OAuth-connected, owned-video, report-first, and limited to validated MVP scope.

## Acceptance criteria

- [ ] Legacy YouTube/Instagram two-video comparison UI is removed from the active creator-facing flow or clearly isolated from MVP routes so it cannot be mistaken for the current product.
- [ ] The default creator-facing route is the OAuth-connected flow: connect YouTube, choose channel, select owned video, submit for review, and view progress/settings.
- [ ] Public URL diagnosis, public surface review, creator-facing Coach LLM report prose, follow-up chat, automated thumbnail vision analysis, payment flow, team/agency workspace, PDF/public share export, and in-app rich report editor are not exposed in the first skeleton.
- [ ] FAQ or equivalent creator-facing copy explains why big channels are not the default benchmark and frames future references as optional study material rather than copy benchmarks.
- [ ] Guardrails prevent external references, comments, public analysis, and thumbnail claims from becoming default evidence paths before their future slices are explicitly implemented.
- [ ] Existing reusable infrastructure such as FastAPI, Next.js, extraction/transcript cache, Groq Whisper fallback, structured errors, backpressure, and provider-mocked tests is retained where it still fits.
- [ ] Tests or checks cover active route rendering, absence of legacy comparison entry points from MVP navigation, FAQ route rendering, and no accidental exposure of out-of-scope product surfaces.

## Blocked by

- Blocked by `issues/001-connect-youtube-oauth-and-session-shell.md`
- Blocked by `issues/003-select-owned-long-form-upload.md`
- Blocked by `issues/004-create-analysis-run-with-honest-progress.md`

## User stories addressed

- User story 43
- User story 44
- User story 94
- User story 95
- User story 96
- User story 97
- User story 98
- User story 99
