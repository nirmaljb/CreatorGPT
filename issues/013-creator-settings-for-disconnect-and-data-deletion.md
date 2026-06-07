## Parent PRD

`issues/prd.md`

## What to build

Add creator settings for connection status, logout, YouTube disconnect, and analysis data deletion. The product should distinguish token revocation from evidence deletion and give creators control over private analytics snapshots and report artifacts.

## Acceptance criteria

- [ ] Creator settings show signed-in identity, selected channel connection state, granted/missing scopes, reconnect-needed state, and available account actions without exposing tokens.
- [ ] Disconnect revokes or invalidates YouTube access where possible, marks the connection disconnected, keeps or deletes analysis data only according to the creator's chosen action, and prevents new analysis until reconnect.
- [ ] Creators can delete a single run's analysis data and all of their analysis data, with server-side authorization and clear confirmation states.
- [ ] Data deletion removes associated snapshots, metric data, baseline records, retention points, transcript chunks, manual evidence, admin notes, exports if stored, concierge report workflow records, feedback, usage ledger entries, and future vector/comment artifacts where present.
- [ ] Logout invalidates the current server-side session without deleting analysis data.
- [ ] Optional account deletion, if implemented in this slice, removes or anonymizes the user and all associated private analysis artifacts according to the documented data policy.
- [ ] Tests cover disconnect behavior, reconnect gating, single-run deletion, all-analysis-data deletion, logout, token non-exposure, authorization boundaries, and removal of associated run artifacts.

## Blocked by

- Blocked by `issues/001-connect-youtube-oauth-and-session-shell.md`
- Blocked by `issues/004-create-analysis-run-with-honest-progress.md`
- Blocked by `issues/006-capture-selected-video-evidence-snapshot.md`
- Blocked by `issues/007-build-baseline-evidence-package.md`
- Blocked by `issues/008-capture-retention-evidence-and-drop-candidates.md`
- Blocked by `issues/009-acquire-transcript-and-map-retention-moments.md`
- Blocked by `issues/010-add-manual-context-and-linked-revision-runs.md`
- Blocked by `issues/011-admin-notes-usage-ledger-and-scoped-export.md`
- Blocked by `issues/012-concierge-report-workflow-and-validation-template.md`

## User stories addressed

- User story 5
- User story 6
- User story 83
- User story 84
- User story 85
- User story 86
- User story 87
