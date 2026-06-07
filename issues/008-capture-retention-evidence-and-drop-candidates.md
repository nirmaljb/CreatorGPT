## Parent PRD

`issues/prd.md`

## What to build

Capture retention evidence for the selected video and baseline where available, store raw retention points, compute lightly smoothed drop candidates, and expose retention quality without overclaiming hook or pacing causes.

## Acceptance criteria

- [ ] Migrations add retention point storage with run ID, video role, timestamp or elapsed ratio, raw value, normalized value, source label, and fetch limitations.
- [ ] The backend fetches selected-video retention and available baseline retention through provider wrappers, then records usage ledger entries for analytics queries and retry/error counts.
- [ ] Retention comparisons align by elapsed video ratio for baseline comparisons and selected-video timestamps for admin evidence display.
- [ ] Drop detection stores candidates based on local drop size and baseline delta, while preserving raw points for inspection.
- [ ] Retention baseline quality is labeled separately from overall baseline quality, and limited retention coverage downgrades hook/pacing confidence state.
- [ ] The admin dashboard shows raw retention points, lightly smoothed drop candidates, first-30-second comparison data, and retention limitations.
- [ ] Tests cover raw retention storage, elapsed-ratio alignment, timestamp display, smoothing, local drop detection, baseline delta detection, hook-window comparisons, retention quality tiers, and confidence downgrade when coverage is limited.

## Blocked by

- Blocked by `issues/007-build-baseline-evidence-package.md`

## User stories addressed

- User story 64
- User story 66
