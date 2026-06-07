## Parent PRD

`issues/prd.md`

## What to build

Create the manual concierge report workflow object and fixed validation template used by admins to prepare, deliver, and evaluate reports outside the app. This is HITL because the fixed report template should be reviewed and approved before implementation so validation data is comparable across creators.

## Acceptance criteria

- [ ] A human-reviewed fixed concierge report template is checked into the repo before workflow implementation and includes evidence quality, what happened, what to preserve, likely weakness, less likely causes, what to ignore, not recommended, metric priority, focused experiments, creative tradeoffs, measurement plan, and draft-labeling guidance.
- [ ] Migrations add concierge report workflow records tied to analysis runs, separate from analysis run status, with status, external draft URL, optional summary, feedback summary, creator delivery timestamps, author, and timestamps.
- [ ] Concierge report statuses include evidence collected, in review, report drafted, sent to creator, feedback received, and closed.
- [ ] The admin dashboard lets admins manage report workflow status, attach an external draft document URL, record summary notes, and capture creator feedback manually.
- [ ] Creator-facing UI only shows simple concierge status and delivery guidance; it does not expose a public automated report UI or in-app rich editor.
- [ ] Feedback fields capture usefulness, perceived alignment with YouTube Studio, style respect, whether the report changed the creator's next decision, willingness to reuse or pay, and notable quotes.
- [ ] The template and workflow reinforce creator-native diagnosis: experiments over prescriptions, no fake certainty, no clickbait pressure, no big-channel default benchmark, and clear labels for optional drafts or rewrites.
- [ ] Tests cover workflow object creation, status transitions, external draft URL storage, feedback summary storage, separation from analysis-run status, creator-safe status display, and admin-only feedback management.

## Blocked by

- Blocked by `issues/011-admin-notes-usage-ledger-and-scoped-export.md`

## User stories addressed

- User story 19
- User story 20
- User story 21
- User story 22
- User story 23
- User story 24
- User story 25
- User story 26
- User story 27
- User story 28
- User story 29
- User story 30
- User story 31
- User story 32
- User story 33
- User story 34
- User story 35
- User story 75
- User story 76
- User story 77
- User story 78
- User story 79
- User story 90
- User story 91
- User story 92
- User story 93
