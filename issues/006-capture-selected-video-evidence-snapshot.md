## Parent PRD

`issues/prd.md`

## What to build

Fetch and store the first reproducible evidence snapshot for the selected video: metadata, public context, first-7-day private analytics when available, and usage ledger entries for the provider work performed.

## Acceptance criteria

- [ ] Migrations add snapshot and metric tables needed to store selected video metadata, normalized first-7-day analytics, evidence source labels, fetch timestamps, and provider limitations.
- [ ] The analysis background task fetches selected video metadata and private YouTube Analytics for the selected channel/video through provider wrappers.
- [ ] The default analytics window is the first 7 completed days after publish; videos between 72 hours and 7 days are labeled as early-read evidence; videos under 72 hours do not receive primary diagnosis-ready status.
- [ ] Stored snapshots are immutable for a run and include enough normalized data to reproduce the evidence shown to admins.
- [ ] The admin dashboard shows selected video title, description, thumbnail, publish date, duration, public stats, private first-7-day metrics, evidence window, source labels, and limitations.
- [ ] The usage ledger records YouTube Data API calls, YouTube Analytics queries, retry/error counts, and provider limitations for the run.
- [ ] Tests cover selected-video metadata capture, analytics-window selection, early-read labeling, under-72-hour handling, immutable snapshots, admin dashboard display, provider-call ledger entries, and no token exposure.

## Blocked by

- Blocked by `issues/004-create-analysis-run-with-honest-progress.md`

## User stories addressed

- User story 58
- User story 59
- User story 74
