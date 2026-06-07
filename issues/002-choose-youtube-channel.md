## Parent PRD

`issues/prd.md`

## What to build

Let an authenticated creator choose which owned YouTube channel to analyze after connecting YouTube. This slice keeps channel identity separate from the user account and makes every downstream action scoped to the selected channel.

## Acceptance criteria

- [ ] The schema and migration support YouTube channel records associated with the authenticated user and OAuth connection.
- [ ] A provider wrapper fetches channel identity data through read-only YouTube access and persists channel IDs, titles, thumbnails where available, and active-channel selection state.
- [ ] A creator with one channel is routed forward with that channel selected, while a creator with multiple channels sees a channel picker before video selection.
- [ ] API responses clearly distinguish no YouTube channel access, incomplete scopes, revoked access, and successful channel discovery.
- [ ] The frontend shows selected-channel state and does not mix channel data between brand accounts.
- [ ] Server-side authorization ensures users can only read and select their own channels.
- [ ] Provider-mocked tests cover one-channel auto-selection, multiple-channel picker behavior, active channel persistence, missing scopes, revoked/incomplete access, and user/channel authorization boundaries.

## Blocked by

- Blocked by `issues/001-connect-youtube-oauth-and-session-shell.md`

## User stories addressed

- User story 11
- User story 86
- User story 87
