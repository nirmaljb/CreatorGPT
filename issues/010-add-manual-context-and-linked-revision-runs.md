## Parent PRD

`issues/prd.md`

## What to build

Let creators and admins add structured manual context that can improve interpretation without mutating existing runs. Manual context revisions and analytics refreshes should create linked runs with explicit reasons and preserve the older evidence package.

## Acceptance criteria

- [ ] Migrations add manual evidence records with structured fields for expected performance, observed problem, intended audience, video goal, channel direction, style/taste constraints, manual metrics, manual transcript reference, optional notes, source actor, and run linkage.
- [ ] Creator-facing and admin-facing forms collect optional targeted context without forcing a long setup form.
- [ ] Manual metrics and user-provided context are labeled separately from fetched platform analytics in APIs, admin views, and exports.
- [ ] Adding interpretation-changing manual context creates a new linked run with `run_reason` set to `manual_context_revision` and does not mutate the previous run snapshots.
- [ ] Refreshing analytics creates a new linked run with `run_reason` set to `refresh` and does not overwrite old evidence.
- [ ] Creator disagreement or missed-context entry is stored respectfully and visible to admins preparing a revised concierge report.
- [ ] Tests cover structured manual context validation, optional targeted forms, manual-vs-platform source labeling, linked manual-context revision runs, linked refresh runs, immutable prior runs, and authorization boundaries.

## Blocked by

- Blocked by `issues/004-create-analysis-run-with-honest-progress.md`

## User stories addressed

- User story 36
- User story 37
- User story 38
- User story 39
- User story 45
- User story 46
- User story 47
- User story 48
- User story 49
- User story 50
- User story 51
- User story 52
