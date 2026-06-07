## Parent PRD

`issues/prd.md`

## What to build

Build and display the creator's own channel baseline for the selected video using recent prior long-form uploads, same-window analytics, median-oriented comparisons, explicit exclusions, and quality labels.

## Acceptance criteria

- [ ] Migrations add baseline membership records with included/excluded status, exclusion reasons, manual override fields, normalized metrics, and baseline quality labels.
- [ ] The backend selects prior long-form videos from the same channel, expands recent-first until enough comparable candidates are found or configured limits are reached, and excludes Shorts, obvious outliers, livestreams, trailers, podcasts, extreme duration mismatches, and other documented distortions.
- [ ] Baseline analytics use the same first-7-day comparison window as the selected video when available, with lifetime metrics treated as secondary context only.
- [ ] Baseline quality is labeled insufficient, limited, usable, or strong with reasons, and fewer than 5 comparable long-form videos prevents confident diagnosis-ready state.
- [ ] The admin dashboard shows included baseline videos, excluded candidates with reasons, baseline quality, baseline metric comparisons, and separate retention-baseline quality placeholders for the retention slice.
- [ ] Admins can edit baseline membership for concierge use and must provide stored override reasons.
- [ ] Learning-mode state is returned when baseline evidence is insufficient rather than forcing a fake diagnosis.
- [ ] Tests cover recent-first candidate selection, backward expansion, same-window metrics, median-oriented comparison data, exclusion reasons, outlier/duration handling, manual overrides, quality labels, and learning-mode gating.

## Blocked by

- Blocked by `issues/006-capture-selected-video-evidence-snapshot.md`

## User stories addressed

- User story 40
- User story 41
- User story 42
- User story 60
- User story 61
- User story 62
- User story 63
- User story 64
