## Problem Statement

The current demo can ingest videos, poll progress, and stream cited answers, but the frontend still exposes too much system fragility to the user. Users can paste a URL that does not match the selected platform, submit malformed links, see technical provider errors, or get stuck in a confusing processing state when the backend fails, stalls, or becomes unreachable. The app also needs clearer retry behavior that does not silently resume stale sessions or pretend to cancel backend work that cannot actually be cancelled yet.

This creates a poor experience during the most important demo path: entering two creator video URLs, waiting for ingestion, and asking comparison questions. The user needs the UI to prevent avoidable mistakes, explain unavoidable failures in plain language, preserve inputs for correction, and never appear frozen.

## Solution

Add a cross-phase error-handling and retry layer for the ingestion and chat experience.

The app will validate URL/platform correctness before ingestion starts, in both the frontend and backend. It will return structured, user-facing error objects for validation, ingestion, backpressure, status, and chat failures. Failed sessions will preserve the user's inputs and show both the overall session error and the specific video error. Retry will create a new session using the current inputs instead of trying to resume or patch the failed session.

The frontend will use a lightweight state machine and stale-response guards so only one major operation can mutate the UI at a time. It will lock inputs during active processing, disable conflicting actions during chat streaming, warn when status polling is slow or stalled, and stop polling terminal sessions. It will display plain-language errors on the page while logging technical details to the console. It will also offer a carefully worded local reset during processing, with confirmation, without claiming the backend task has stopped.

## User Stories

1. As a demo user, I want the app to reject an Instagram option paired with a YouTube URL, so that I know what to fix before ingestion starts.
2. As a demo user, I want the app to reject a YouTube option paired with an Instagram URL, so that I do not wait for a backend failure that could have been prevented.
3. As a demo user, I want Instagram validation to accept Reels only, so that the app stays aligned with the supported assignment flow.
4. As a demo user, I want YouTube validation to accept common YouTube URL forms, so that normal pasted YouTube links work.
5. As a demo user, I want pasted URLs to be trimmed, so that accidental spaces do not break ingestion.
6. As a demo user, I want query strings on YouTube and Instagram URLs to be allowed, so that copied share links still work.
7. As a demo user, I want validation messages to appear after I interact with a field or submit the form, so that the initial page does not feel noisy.
8. As a demo user, I want invalid fields to show clear inline messages, so that I know exactly which video URL needs attention.
9. As a demo user, I want the submit button disabled while inputs are invalid, so that I cannot start a bad ingest by mistake.
10. As a demo user, I want duplicate URLs to show a warning without blocking submission, so that I can still test same-video behavior if needed.
11. As a demo user, I want both videos to be allowed to use the same platform, so that I can compare two YouTube videos or two Instagram Reels when needed.
12. As a demo user, I want the app to preserve my URLs after ingestion fails, so that I can edit and retry without pasting them again.
13. As a demo user, I want retry to start a new comparison session, so that stale state from the failed session does not pollute the next attempt.
14. As a demo user, I want retry to reuse cached real extraction results by default, so that repeated demos are faster and more stable.
15. As a demo user, I want the app to block chat when one video failed, so that comparison answers are not based on partial evidence.
16. As a demo user, I want the successful video card to remain visible when the other video fails, so that I can still inspect what did work.
17. As a demo user, I want a session-level error to explain why I cannot continue, so that the overall state is clear.
18. As a demo user, I want per-video errors on the relevant video card, so that I know which URL or platform caused the problem.
19. As a demo user, I want Instagram access failures to mention privacy, unavailability, or cookies, so that I understand why a public-looking Reel may fail.
20. As a demo user, I want technical provider errors hidden from the page, so that the UI stays understandable.
21. As a developer, I want technical errors logged in the backend console, so that I can debug provider, database, and vector store failures.
22. As a developer, I want the frontend console to log structured error details, so that I can debug browser-side failures without exposing internals in the UI.
23. As a demo user, I want the app to show a friendly busy message when ingestion capacity is full, so that I know the system is not broken.
24. As a demo user, I want rate-limit responses with retry timing to show a countdown, so that I know when to try again.
25. As a demo user, I want retry disabled until a rate-limit countdown ends, so that I do not repeatedly submit doomed requests.
26. As a demo user, I want network loss to be treated separately from ingestion failure, so that offline conditions do not look like failed videos.
27. As a demo user, I want polling to resume when the browser comes back online, so that I do not need to refresh manually.
28. As a demo user, I want slow status requests to show a connection warning, so that the interface does not appear frozen.
29. As a demo user, I want the app to warn after 60 seconds without progress movement, so that I know it is still checking.
30. As a demo user, I want the frontend stalled warning to be non-terminal, so that the backend remains the source of truth for failure.
31. As a demo user, I want backend stale-session detection to produce the real failed state, so that stopped background tasks become visible.
32. As a demo user, I want inputs locked while ingestion is processing, so that the visible form cannot drift from the backend job.
33. As a demo user, I want a local reset option during processing, so that I can clear the page if I no longer care about the current job.
34. As a demo user, I want local reset to confirm that backend processing may continue, so that I do not mistake it for cancellation.
35. As a demo user, I want completed results to remain visible while I edit inputs for a new comparison, so that I do not lose the answer history prematurely.
36. As a demo user, I want the app to show that a new comparison is pending after I edit completed inputs, so that I understand which session chat is tied to.
37. As a demo user, I want starting a new comparison to clear the old result only after submit, so that editing fields is not destructive.
38. As a demo user, I want chat disabled until ingestion reaches a terminal successful state, so that questions are answered only after evidence is ready.
39. As a demo user, I want start-ingest disabled while chat is streaming, so that one operation cannot corrupt another operation's state.
40. As a demo user, I want resetting during chat streaming to abort the active stream and clear the draft, so that no hanging answer remains.
41. As a demo user, I want chat stream errors to replace the assistant draft with a friendly failure message, so that I never see permanent "Streaming..." text.
42. As a demo user, I want the original user question to remain visible after a chat failure, so that I can resend it if I choose.
43. As a demo user, I want no dedicated chat retry button for now, so that the UI remains simple.
44. As a developer, I want structured error codes, messages, scopes, and retryability, so that frontend behavior does not depend on parsing raw strings.
45. As a developer, I want structured session errors persisted, so that refresh and status polling keep the same failure meaning.
46. As a developer, I want structured video errors persisted, so that each video card can reconstruct its failure state reliably.
47. As a developer, I want existing string error fields preserved, so that current consumers and tests remain compatible during migration.
48. As a developer, I want validation to run before session creation, slot acquisition, or rate-limit counting, so that invalid inputs do not consume backend capacity.
49. As a developer, I want invalid platform/URL mismatches to return 422, so that they align with request validation semantics.
50. As a developer, I want app-owned API errors to use a consistent response envelope, so that the frontend can parse all failures uniformly.
51. As a developer, I want the frontend to tolerate older error response shapes, so that existing backend paths do not break the page during incremental migration.
52. As a developer, I want validation and error parsing extracted into pure helper modules, so that future tests can cover them cheaply.
53. As a developer, I want backend validation and app error helpers extracted, so that route handlers stay thin and testable.
54. As a developer, I want stage-owned error categorization first, so that metadata, transcript, vector, rate-limit, and validation failures get accurate codes.
55. As a developer, I want a fallback error classifier for unknown provider failures, so that the UI still gets a safe plain-language message.
56. As a reviewer, I want frontend lint, typecheck, and build to pass after the change, so that the UI remains production-safe.
57. As a reviewer, I want backend tests to cover URL validation and structured error behavior, so that the high-risk failure paths are protected.
58. As a reviewer, I want docs and progress updated, so that future implementation work understands the retry and error-handling decisions.

## Implementation Decisions

- Implement this as a cross-phase patch. The user-facing states belong mainly to Product UI work, while structured errors, no-hang behavior, and retry/backpressure behavior belong mainly to Resilience and Demo Readiness.
- Add frontend URL validation for selected platform and URL shape before ingestion.
- Add backend URL validation for selected platform and URL shape before session creation, ingestion slot acquisition, or rate-limit accounting.
- YouTube validation accepts common watch, short, and short-domain URL forms.
- Instagram validation accepts Reels only for now.
- Safe URL normalization trims whitespace, accepts uppercase hosts through validation normalization, and allows query strings.
- The system will not guess platforms from URLs, rewrite links, expand shortened links, or run frontend reachability checks.
- Both videos may use the same platform.
- Duplicate URLs produce a warning but do not block submission.
- Retry means whole-session retry. It creates a new session using the current inputs.
- Retry does not implement per-video retry, job resume, or backend cancellation.
- Retry reuses the extraction cache by default. There is no frontend force-refresh toggle.
- Failed ingestion preserves editable inputs.
- Completed ingestion stores the submitted inputs separately from current editable inputs so the UI can detect a pending new comparison.
- Partial ingestion success does not unlock chat. Comparison chat requires both videos to complete successfully.
- The frontend displays both session-level and per-video errors.
- The backend owns user-facing error translation. Raw technical details stay in logs and debug paths.
- App-owned errors use a structured envelope with code, message, scope, optional video ID, optional field, and retryability.
- Existing string error fields remain for compatibility while structured fields are added.
- Minimal structured error fields are persisted for sessions and videos.
- Retry is shown for retryable errors. Start-over/edit behavior is used for non-retryable validation or configuration errors.
- Rate-limit countdown is shown only when the backend returns retry timing.
- The frontend gets a lightweight state machine for idle, validating, submitting, processing, completed, failed, offline, and chatting states.
- The frontend uses active request/session guards so stale responses cannot mutate the wrong UI state.
- Inputs and platform selectors are locked during active submission and processing.
- Starting a new ingest is blocked while chat is streaming.
- Status polling stops on failed, completed, or ready statuses.
- The frontend stalled warning appears after 60 seconds without movement in current step, progress percent, or status timestamp.
- The frontend stalled warning is informational only. The backend status endpoint remains the source of truth for marking sessions failed.
- During processing, the UI may offer a local reset action. It must not say cancel and must confirm that backend processing may continue.
- Chat SSE errors use the same structured error model as ingestion errors.
- Chat stream failures replace any empty assistant draft with a friendly error message and never leave permanent streaming placeholder text.
- No raw technical errors appear in the main page. The frontend logs structured/raw details to the browser console.
- Backend error categorization is stage-owned first, with a fallback classifier for unknown provider text.
- Mention cookies only for Instagram-specific access failures.
- Extract frontend validation and error parsing into small pure modules.
- Extract backend validation and app error helpers into small modules.
- Keep route handlers focused on validation, backpressure/rate-limit enforcement, session creation, and background task launch.
- Update the agent decisions, phase plans, phase docs, and progress log after implementation chunks.

## Testing Decisions

- Good tests should assert externally visible behavior: API status codes, response envelopes, persisted structured error state, retryability flags, frontend validation outputs, and UI-safe state transitions.
- Tests should avoid asserting private implementation details such as exact helper function internals or raw provider exception strings.
- Backend tests should cover accepted YouTube URL forms.
- Backend tests should cover accepted Instagram Reel URL forms.
- Backend tests should reject platform/URL mismatches with 422.
- Backend tests should reject unsupported Instagram non-Reel URLs with 422.
- Backend tests should verify validation happens before ingestion slot acquisition, session creation, and rate-limit accounting.
- Backend tests should verify structured app error envelopes for validation and rate-limit paths.
- Backend tests should verify persisted session and video error fields can be returned through status responses.
- Backend tests should verify known pipeline failure categories map to user-facing codes and retryability.
- Backend tests should verify fallback unknown errors are sanitized.
- Chat stream tests should verify SSE error events use the structured model and do not terminate with an unparseable broken stream.
- Existing test prior art includes mocked FastAPI smoke tests, backpressure tests, stale ingest tests, status endpoint tests, assignment eval tests, and chat stream service tests.
- Frontend validation should be extracted so it can be tested later without rendering the full page.
- For this pass, frontend verification must at least include lint, typecheck, and build.
- Do not add a frontend test runner solely for this change unless the team decides the added dependency is worth it.
- End-to-end real provider tests remain manual or nightly, not required for every commit.

## Out of Scope

- Durable job queues.
- Backend cancellation.
- Per-video retry.
- Resuming failed or stale sessions.
- A frontend force-refresh toggle for extractor cache.
- Frontend URL reachability checks.
- Authentication or user accounts.
- Distributed rate limiting.
- Custom modal components for reset confirmation.
- Dedicated retry button for individual failed chat messages.
- New provider integrations.
- Reranking, hybrid retrieval, or retrieval quality changes.

## Further Notes

- This PRD follows the decisions made during the error-handling design interview.
- The highest-risk implementation areas are stale frontend responses, partial ingestion failures, and preserving clear separation between user-facing error text and raw technical logs.
- The feature should improve the demo path without changing the core RAG routing or retrieval behavior.
