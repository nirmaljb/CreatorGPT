## Parent PRD

`issues/prd.md`

## What to build

Give admins the internal tools needed to prepare concierge reports from one run's evidence: notes on evidence moments, a visible usage ledger, and a sanitized scoped export.

## Acceptance criteria

- [ ] Migrations add admin note records linked to run evidence moments, baseline comparisons, preserve candidates, experiment candidates, or general run review sections.
- [ ] Admin notes remain internal by default in the app and are labeled as admin-authored interpretation when included in exports.
- [ ] The admin dashboard supports creating, editing, and viewing notes on retention moments, transcript intervals, baseline rows, and general report-prep sections.
- [ ] The usage ledger is visible in the admin dashboard and includes API call counts, analytics query counts, transcript source, transcribed seconds, comment fetch counts when implemented, chunk counts, embedding counts when implemented, retry counts, and error counts.
- [ ] Admins can export a sanitized evidence package for exactly one analysis run, including normalized evidence, source labels, limitations, selected admin notes, and manual evidence labels.
- [ ] Exports exclude OAuth tokens, raw OAuth payloads, unrelated channel data, unrelated user data, and secrets.
- [ ] Tests cover admin note persistence, internal-default visibility, export inclusion of normalized evidence and notes, one-run scoping, usage ledger display, and exclusion of tokens/raw OAuth/unrelated data.

## Blocked by

- Blocked by `issues/005-admin-run-list-and-access-boundary.md`
- Blocked by `issues/006-capture-selected-video-evidence-snapshot.md`
- Blocked by `issues/007-build-baseline-evidence-package.md`
- Blocked by `issues/008-capture-retention-evidence-and-drop-candidates.md`
- Blocked by `issues/009-acquire-transcript-and-map-retention-moments.md`

## User stories addressed

- User story 69
- User story 70
- User story 71
- User story 72
- User story 73
- User story 74
- User story 80
