## Parent PRD

`issues/prd.md`

## What to build

Add manual selection of one owned long-form upload for the selected channel. The app should show lightweight upload metadata, verify ownership server-side, reject Shorts from the long-form workflow, and avoid precomputing private analytics across all uploads.

## Acceptance criteria

- [ ] A YouTube provider wrapper lists recent owned uploads for the selected channel with lightweight metadata only, such as video ID, title, thumbnail, publish date, duration, and public stats where available.
- [ ] The creator-facing UI lets the creator manually choose one video and makes clear that Shorts are not supported by the long-form diagnosis workflow.
- [ ] The backend verifies the submitted video belongs to the authenticated selected channel before any analysis run can be created.
- [ ] Shorts detection rejects Shorts with a clear creator-facing state instead of sending them into long-form analysis.
- [ ] The upload list path does not fetch private analytics for every upload or auto-rank underperforming videos.
- [ ] Server-side authorization prevents users from selecting videos from channels they do not own through their current session.
- [ ] Provider-mocked tests cover owned-upload listing, lightweight metadata rendering, ownership verification, Shorts exclusion, no analytics precomputation, and selected-channel scoping.

## Blocked by

- Blocked by `issues/002-choose-youtube-channel.md`

## User stories addressed

- User story 12
- User story 13
- User story 14
- User story 15
