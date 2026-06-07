## Parent PRD

`issues/prd.md`

## What to build

Add explicit admin-only routes for concierge operations, starting with a run list and dashboard shell. This slice creates the authorization boundary needed before richer evidence data is exposed internally.

## Acceptance criteria

- [ ] Admin access is controlled server-side by an environment allowlist by email, with optional Google subject allowlist if configured.
- [ ] Admin API routes are explicit and reject unauthenticated users and authenticated non-admin users without leaking run data.
- [ ] The admin run list shows submitted analysis runs with creator identity, selected channel/video summary, run status, report workflow state when present, created time, updated time, and sanitized failure summary.
- [ ] Admin filters support at least run status and report workflow state, with sensible empty states.
- [ ] An admin dashboard shell opens for one run and shows authorization-safe placeholders for evidence sections that later slices will fill.
- [ ] Provider and backend errors shown to admins are sanitized and do not include raw tokens, OAuth payloads, or secrets.
- [ ] Tests cover admin allowlist behavior, non-admin rejection, explicit admin route authorization, status/workflow filtering, dashboard shell access, and sanitized error display.

## Blocked by

- Blocked by `issues/004-create-analysis-run-with-honest-progress.md`

## User stories addressed

- User story 55
- User story 56
- User story 57
- User story 80
- User story 81
- User story 82
