## Parent PRD

`issues/prd.md`

## What to build

Build the first creator-facing "Connect YouTube" path from the app UI through first-party Google OAuth/OIDC, server-side session creation, and a connection status response. This slice establishes the secure auth foundation from the PRD's OAuth, privacy, implementation, and testing decisions without starting analysis yet.

## Acceptance criteria

- [ ] The app has Alembic configured and an initial migration for users, server-side sessions, OAuth token records, and any auth support tables needed by this slice.
- [ ] The creator-facing UI presents one clear "Connect YouTube" action with plain-language scope explanation and no separate email/password, magic link, anonymous, or vendor-auth flow.
- [ ] OAuth start requests only identity, YouTube read-only, and YouTube Analytics read-only scopes; revenue, write, upload, delete, and management scopes are not requested.
- [ ] OAuth callback validates state, validates Google identity through a provider wrapper, records exact granted scopes, creates or updates the user from Google subject, and creates an HTTP-only server-side session.
- [ ] Refresh tokens are encrypted before storage; access tokens are not persisted by default; no token or raw OAuth credential is returned to frontend APIs or logged in provider errors.
- [ ] `GET /me` exposes session identity, connection status, granted/missing scopes, and reconnect-needed state without exposing tokens.
- [ ] Browser mutations in this slice use CSRF protection, and credentialed CORS is limited to explicit configured origins.
- [ ] Provider-mocked backend tests cover OAuth state validation, scope tracking, incomplete connection state, session creation, reconnect state, token safety, CORS/CSRF behavior, and frontend rendering/type checks where dependencies are available.

## Blocked by

None - can start immediately

## User stories addressed

- User story 1
- User story 2
- User story 3
- User story 4
- User story 7
- User story 8
- User story 9
- User story 10
- User story 83
- User story 84
- User story 85
- User story 86
- User story 87
- User story 88
- User story 89
- User story 100
