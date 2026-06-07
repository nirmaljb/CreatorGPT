## Problem Statement

Thoughtful YouTube creators often know a video underperformed, but they do not know what to change next without damaging the creative taste, voice, and channel identity they are trying to build. YouTube Studio exposes metrics, but it does not clearly translate those metrics into a creator-native diagnosis: what happened, what likely mattered, what to preserve, what to ignore, and what experiment to run next.

Most creator AI tools risk making this worse. They push broad "viral" formulas, big-channel imitation, generic clickbait titles, and surface-level advice that does not respect the creator's own audience, intent, evidence, or style. The product must avoid becoming another tool that helps creators mass-produce generic AI content.

The immediate product problem is to build the first reliable, OAuth-connected data skeleton that can collect the private YouTube evidence needed for high-quality manual concierge reports. The first milestone should not attempt a full automated diagnosis engine or public report generator. It should provide trustworthy data capture, reproducible snapshots, an admin-only evidence dashboard, and an operational workflow for preparing and validating manual reports with real creators.

## Solution

Build an OAuth-connected YouTube analysis skeleton for concierge validation.

A creator connects YouTube with Google OAuth, grants narrow read-only YouTube and YouTube Analytics scopes, selects one owned long-form video, and optionally provides lightweight creator intent/context. The backend creates an immutable analysis run, fetches selected-video analytics, builds a recent channel-relative baseline, fetches retention data when available, acquires a selected-video transcript, maps retention intervals to transcript timestamps, and stores a reproducible evidence package.

The first creator-facing experience is simple: connect YouTube, choose a channel/video, submit the video for review, and see high-level progress states. The first admin experience is richer: inspect runs, review baseline membership, see retention and transcript evidence, edit admin-only baseline membership, add notes, export scoped evidence, and track the manual concierge report workflow.

Concierge reports are prepared manually from the internal evidence package and delivered by doc/email with optional live calls. This validates whether the product's core value is real before building the full deterministic diagnosis engine and Coach LLM. The validated report philosophy is creator-native: diagnose against the creator's own channel, intent, audience, and evidence; avoid default big-channel comparison; preserve strengths and taste; recommend experiments rather than prescriptive slop; and never overclaim what the data can prove.

## User Stories

1. As a thoughtful YouTube creator, I want to connect my YouTube account securely, so that the product can analyze my own private channel signals.
2. As a thoughtful YouTube creator, I want the app to explain requested scopes in plain language, so that I understand what access I am granting.
3. As a thoughtful YouTube creator, I want the app to use read-only scopes only, so that I know it cannot edit, upload, delete, or manage my videos.
4. As a thoughtful YouTube creator, I want the app to avoid revenue scopes, so that sensitive monetization data is not part of the MVP.
5. As a thoughtful YouTube creator, I want to disconnect YouTube at any time, so that I can revoke access when I no longer want the product connected.
6. As a thoughtful YouTube creator, I want to delete analysis data, so that I control private analytics snapshots and report artifacts.
7. As a thoughtful YouTube creator, I want to sign in with Google only, so that the account flow matches the YouTube analytics workflow.
8. As a thoughtful YouTube creator, I want one clear "Connect YouTube" flow, so that I do not have to separately understand identity login and analytics consent.
9. As a thoughtful YouTube creator, I want the app to tell me if YouTube access is incomplete, so that I know why diagnosis cannot proceed.
10. As a thoughtful YouTube creator, I want a reconnect flow if access expires or is revoked, so that I can restore analysis without confusing errors.
11. As a thoughtful YouTube creator with multiple channels, I want to choose the channel to analyze, so that the app does not mix data between brand accounts.
12. As a thoughtful YouTube creator, I want to select one owned video manually, so that I can focus on the video I care about.
13. As a thoughtful YouTube creator, I want the app to list my recent owned uploads with lightweight metadata, so that I can choose the correct video.
14. As a thoughtful YouTube creator, I want the app to avoid scanning and auto-ranking all my uploads by default, so that it does not over-collect private analytics.
15. As a thoughtful YouTube creator, I want the MVP to reject Shorts from long-form diagnosis, so that it does not apply the wrong performance model.
16. As a thoughtful YouTube creator, I want simple progress states after submitting a video, so that I know evidence collection is moving forward.
17. As a thoughtful YouTube creator, I do not want fake progress percentages, so that the product remains honest about multi-provider work.
18. As a thoughtful YouTube creator, I want to know when evidence has been collected, so that I understand the manual report is being prepared.
19. As a thoughtful YouTube creator, I want the manual report delivered clearly by doc or email, so that I can review the findings without needing unfinished product UI.
20. As a thoughtful YouTube creator, I want the report to explain evidence quality, so that I know what the analysis can and cannot support.
21. As a thoughtful YouTube creator, I want the report to tell me what happened to the video, so that I can understand the performance issue.
22. As a thoughtful YouTube creator, I want the report to separate performance diagnosis from creative judgment, so that my creative choices are not dismissed as "bad" just because one metric underperformed.
23. As a thoughtful YouTube creator, I want the report to show what to preserve, so that I do not overcorrect and lose what is already working.
24. As a thoughtful YouTube creator, I want the report to say when it cannot identify strengths confidently, so that I do not receive generic praise.
25. As a thoughtful YouTube creator, I want the report to show the likely weakness or friction point, so that I can focus my next experiment.
26. As a thoughtful YouTube creator, I want the report to explain less likely causes, so that I do not chase the wrong fix.
27. As a thoughtful YouTube creator, I want "what to ignore" guidance, so that I do not overfocus on metrics that were not the bottleneck.
28. As a thoughtful YouTube creator, I want a "not recommended" section, so that I can avoid tempting but misleading optimizations.
29. As a thoughtful YouTube creator, I want metric priority, so that I know which signal to watch first.
30. As a thoughtful YouTube creator, I want recommendations framed as experiments, so that the product respects uncertainty and creative judgment.
31. As a thoughtful YouTube creator, I want a primary experiment and a small number of secondary experiments, so that the action plan is focused.
32. As a thoughtful YouTube creator, I want every experiment to include a creative tradeoff, so that I know what might be lost by optimizing.
33. As a thoughtful YouTube creator, I want experiments to include how to measure success, so that I can learn from the next upload.
34. As a thoughtful YouTube creator, I want optional draft hooks or titles to be labeled as drafts, so that I do not mistake them for guaranteed answers.
35. As a thoughtful YouTube creator, I want generated options to avoid fake stakes and exaggerated promises, so that the advice does not turn my video into clickbait.
36. As a thoughtful YouTube creator, I want the product to preserve my stated style/taste constraints, so that recommendations still feel like my channel.
37. As a thoughtful YouTube creator, I want style drift warnings, so that I can see when an optimization may move my channel away from my intent.
38. As a thoughtful YouTube creator, I want goal-aware interpretation, so that a low-view educational or trust-building video is not treated the same as a growth-focused upload.
39. As a thoughtful YouTube creator, I want audience-goal-specific guidance when relevant, so that advice can differ for existing-audience and new-audience goals.
40. As a thoughtful YouTube creator, I want the product to use my own channel baseline by default, so that I am not compared against unrelated big creators.
41. As a thoughtful YouTube creator without enough history, I want a learning-mode report instead of a fake diagnosis, so that I still get useful guidance without false confidence.
42. As a starting creator, I want observations and experiments based on my selected video, so that I can improve without being told to copy larger channels.
43. As a thoughtful YouTube creator, I want external references to be optional and user-invoked, so that references are study material rather than default benchmarks.
44. As a thoughtful YouTube creator, I want the product to explain why big channels are not the default comparison, so that I trust the creator-native approach.
45. As a thoughtful YouTube creator, I want manual context to be optional and targeted, so that I am not forced through a long setup form.
46. As a thoughtful YouTube creator, I want to provide my intended audience when it matters, so that topic-audience mismatch can be interpreted more honestly.
47. As a thoughtful YouTube creator, I want to provide the goal of a video, so that the report can distinguish growth, trust, education, entertainment, conversion, and experimentation.
48. As a thoughtful YouTube creator, I want to say what kind of channel I am trying to build, so that recommendations are not generic.
49. As a thoughtful YouTube creator, I want to say what I do not want my channel to become, so that the product avoids misaligned advice.
50. As a thoughtful YouTube creator, I want to disagree with a diagnosis or add missed context, so that the analysis can be revised respectfully.
51. As a thoughtful YouTube creator, I want revisions to create linked runs, so that older reports remain reproducible.
52. As a thoughtful YouTube creator, I want refreshes to create linked runs, so that updated analytics do not silently overwrite old evidence.
53. As a thoughtful YouTube creator, I want failed runs to be retryable, so that transient provider failures do not permanently block me.
54. As a thoughtful YouTube creator, I want retries to create linked runs, so that failure history remains auditable.
55. As an admin, I want to see all submitted analysis runs, so that I can manage concierge operations.
56. As an admin, I want to filter runs by status and report workflow state, so that I can find work needing review.
57. As an admin, I want to open an evidence dashboard for a run, so that I can prepare a manual report from stored evidence.
58. As an admin, I want to see selected video metadata, title, description, thumbnail, publish date, duration, and public stats, so that I understand the video context.
59. As an admin, I want to see private first-7-day analytics, so that I can compare the video against its real performance window.
60. As an admin, I want to see baseline membership and exclusion reasons, so that I can judge baseline quality.
61. As an admin, I want to edit baseline membership for concierge use, so that manual reports can handle cases automation does not yet understand.
62. As an admin, I want excluded baseline candidates shown separately, so that I can debug why the baseline is limited.
63. As an admin, I want baseline quality labels and reasons, so that I know whether diagnosis claims are safe.
64. As an admin, I want retention baseline quality separately from overall baseline quality, so that hook/pacing claims are properly constrained.
65. As an admin, I want transcript coverage quality, so that I know which retention intervals can be interpreted.
66. As an admin, I want raw retention points and lightly smoothed drop detection, so that I can inspect the evidence behind drop candidates.
67. As an admin, I want retention drops mapped to transcript intervals, so that I can see what viewers were watching at those moments.
68. As an admin, I want an embedded YouTube player with timestamp jumps, so that I can inspect evidence quickly.
69. As an admin, I want manual notes per evidence moment, so that I can capture report interpretation while reviewing data.
70. As an admin, I want admin notes to remain internal by default, so that rough notes are not exposed to creators.
71. As an admin, I want admin notes in evidence exports, so that manual report preparation can move into docs or spreadsheets.
72. As an admin, I want scoped evidence export for one run, so that I can prepare concierge reports outside the app.
73. As an admin, I want exports to exclude tokens and unrelated channel data, so that private access is not leaked.
74. As an admin, I want a lightweight usage ledger per run, so that I can track quota, transcription, embedding, and provider costs.
75. As an admin, I want a separate concierge report workflow object, so that manual report delivery is tracked independently from evidence collection.
76. As an admin, I want concierge report statuses, so that I can track evidence collected, in review, drafted, sent, feedback received, and closed.
77. As an admin, I want to attach an external draft document URL, so that reports can be written quickly without building an in-app editor.
78. As an admin, I want to manually capture creator feedback, so that validation data is preserved without forcing in-app feedback during concierge.
79. As an admin, I want to record whether the report was useful, matched YouTube Studio, respected style, changed the next decision, and created willingness to reuse or pay, so that concierge validation is measurable.
80. As an admin, I want sanitized provider errors, so that I can debug issues without exposing raw credentials.
81. As an admin, I want admin access controlled by an allowlist, so that internal evidence dashboards are not exposed to normal users.
82. As an admin, I want admin routes to be explicit, so that authorization boundaries are clear and testable.
83. As a system operator, I want server-side sessions, so that auth can be revoked and checked reliably.
84. As a system operator, I want refresh tokens encrypted at rest, so that YouTube access is protected.
85. As a system operator, I want access tokens kept out of persistent storage by default, so that token exposure is minimized.
86. As a system operator, I want exact granted-scope tracking, so that analysis only starts when required scopes are actually present.
87. As a system operator, I want token validation before analysis, so that revoked or incomplete connections fail early and clearly.
88. As a system operator, I want CSRF protection for browser mutations, so that cookie-based auth is protected.
89. As a system operator, I want strict CORS origins, so that credentialed browser requests are not allowed from arbitrary sites.
90. As a product owner, I want manual concierge validation before full automation, so that the automated product is based on reports creators actually trust.
91. As a product owner, I want fixed report templates during concierge, so that validation results are comparable across creators.
92. As a product owner, I want limited evidence visuals in concierge reports, so that reports build trust without recreating YouTube Studio dashboards.
93. As a product owner, I want the first skeleton to stop at an internal evidence dashboard, so that public report UI is not built before the report format is validated.
94. As a product owner, I want no payment flow before concierge validation, so that the team focuses on data quality and report usefulness.
95. As a product owner, I want no team or agency workspace in MVP, so that the first workflow stays focused on individual creators.
96. As a product owner, I want no public URL diagnosis in MVP, so that the product promise remains tied to private analytics and channel baseline.
97. As a product owner, I want no automated thumbnail vision analysis in MVP, so that the product does not make unsupported visual claims.
98. As a product owner, I want no creator-facing Coach LLM in the first skeleton, so that manual reports can validate the product brain first.
99. As a product owner, I want comments deferred until the analytics/retention/transcript skeleton works, so that supporting evidence does not distract from core evidence.
100. As a product owner, I want first-party Google OAuth and DB sessions instead of a vendor auth platform for MVP, so that YouTube token custody and server-side analytics access remain explicit.

## Implementation Decisions

- The first implementation milestone is an OAuth-connected concierge skeleton, not the full public automated diagnosis product.
- The creator-facing MVP skeleton uses Google OAuth only. Email/password, magic links, anonymous accounts, and third-party hosted auth are out for the first skeleton.
- The product uses a first-party auth layer with Google OAuth/OIDC provider validation and server-side sessions.
- The OAuth flow combines identity and YouTube consent in one "Connect YouTube" action because YouTube access is required for the core workflow.
- The required scopes are identity, YouTube read-only, and YouTube Analytics read-only. Monetary analytics and write/manage scopes are not requested.
- OAuth consent can run in Google Testing mode with allowlisted concierge users.
- Valid Google identity can create or update a user, but missing YouTube scopes creates an incomplete connection state and cannot start analysis.
- OAuth token records track exact granted scopes, missing required scopes, connection status, and last verification time.
- Refresh tokens are encrypted at rest with an app-level encryption key for MVP. Managed KMS is deferred until broader launch.
- Access tokens are generated server-side when needed and are not persisted by default.
- Server-side user sessions are stored with opaque cookie tokens. Cookies are HTTP-only and protected with secure/same-site settings appropriate to environment.
- Browser mutations use CSRF protection. OAuth callback validates OAuth state.
- CORS origins are explicit and do not use wildcard credentials.
- Admin access uses an environment allowlist by email, with optional Google subject allowlist.
- Admin routes are explicit and server-side protected.
- The creator-facing skeleton route is separated from admin and FAQ surfaces. OAuth callback redirects into the creator-facing app flow.
- The legacy A/B comparison UI should be replaced during skeleton implementation, not as a planning-only change.
- The app supports multiple YouTube channels per Google account at schema/provider/UI-picker level. One active channel is selected for the MVP flow.
- The upload list is manual selection only. It shows lightweight metadata and does not precompute private analytics across every upload.
- The selected video must be owned by the authenticated selected channel.
- MVP diagnosis is long-form-only. Shorts are detected and excluded from the long-form analysis workflow.
- Analysis execution uses FastAPI background tasks for the first skeleton, not a durable queue. The run state machine remains queue-ready.
- Analysis run statuses include queued, running, needs input, completed, and failed.
- Creator-facing progress uses step labels, not exact percentages. Admin views can show detailed progress and bounded step completion.
- Failed-run retry creates a new linked analysis run rather than mutating the failed run.
- Refresh and interpretation-changing manual context create linked runs with explicit run reasons.
- Initial run reasons include initial, retry, refresh, manual context revision, and deeper analysis.
- The first migration work starts with Alembic before adding new canonical tables.
- Migrations are incremental. Auth, session, channel, OAuth token, analysis run, and usage ledger tables come first; snapshot/report/feedback tables are added as implementation requires them.
- OAuth tokens are per user and provider. YouTube channels are separate records associated with the user.
- One Google account maps to one app user for MVP. Account linking is deferred.
- Google subject is the stable identity. Email, name, and avatar update on login.
- The first skeleton supports disconnect and delete analysis data paths before broader testing.
- On disconnect, the product should distinguish token revocation from analysis data deletion.
- The first skeleton includes minimal settings for connection state, disconnect, delete analysis data, logout, and possibly account deletion.
- Analysis snapshots are immutable. Reports, citations, feedback, and manual context revisions link to the run that produced them.
- The default comparison window is first 7 completed days after publish.
- Videos between 72 hours and 7 days old can produce lower-confidence early-read evidence. Videos under 72 hours generally do not receive a primary bottleneck.
- Baselines are recent-first, same-window, long-form-only, median-oriented, and expanded backward until enough comparable prior videos are found or candidate limits are reached.
- Baseline quality uses labels with reasons instead of numeric scores.
- Baseline quality gates report type: insufficient means learning report, limited means hypotheses only, usable/strong can support diagnosis if other gates pass.
- Admin dashboard supports manual baseline membership editing during concierge validation, with stored override reasons.
- Excluded baseline candidates remain visible to admins with reasons.
- Baseline filtering after major channel changes is user-confirmed or admin/manual-context-driven, not silently inferred from vague LLM guesses.
- Primary baseline uses first-7-day metrics. Lifetime metrics are secondary context only and do not drive primary bottleneck scoring.
- Baseline metrics include views, watch time, average view duration or percentage, engagement per view, subscriber impact where available, and retention summary where available.
- Retention curves are first-skeleton priority if API access allows.
- Retention baseline quality is separate from overall baseline quality.
- Retention comparisons align by elapsed video ratio for baseline comparisons and selected-video timestamps for evidence display.
- Retention drop detection uses both local drop size and baseline delta.
- Raw retention points are stored and visible in admin. Light smoothing may be computed for drop detection.
- Strong retention claims require enough retention baseline coverage. Limited retention coverage downgrades hook/pacing confidence.
- Selected-video transcript ingestion is first-skeleton scope.
- Transcript acquisition tries the existing YouTube transcript/caption fast path, then Whisper fallback, then optional manual transcript/script.
- Stronger private caption-management scopes are not requested in MVP.
- Whisper fallback has a configurable transcription cap with explicit limitations and admin override.
- Retention-to-transcript mapping requires transcript coverage for the interval being interpreted.
- Transcript chunks are stored for the selected video. Embeddings are deferred until retrieval, follow-up chat, or deeper comparison needs them.
- Baseline videos use analytics and metadata only by default. Baseline transcripts are not pulled automatically.
- Selective deeper transcript analysis can pull reference or baseline transcripts after explicit user/admin confirmation.
- Deeper transcript analysis creates a linked run and lists all additional videos analyzed.
- User-selected same-channel references are supported before automated reference selection. Suggested candidates can be offered with evidence-backed labels.
- Candidate labels must be metric-specific and cited. Public views can support higher views, not higher retention.
- Comments are supporting evidence and can wait until analytics, retention, transcript mapping, and the internal dashboard are reliable.
- When comments are implemented, they are fetched through YouTube Data API, capped, stored as raw sample plus derived signals, and handled as neutral when disabled or unavailable.
- The Audience Signals Agent is deterministic-first, with optional admin-reviewed LLM clustering later.
- Audience Signals Agent output is compact structured JSON and does not dump raw comments into the main diagnosis context.
- Comments are audience-response evidence only, not creator identity evidence.
- The first skeleton has no creator-facing Coach LLM report. Optional internal LLM helpers may be used only for admin-reviewed notes.
- Deterministic diagnosis automation and public report UI come after concierge validation.
- The internal dashboard includes selected video metadata, thumbnail display, embedded YouTube player, retention charts, baseline tables, transcript mapping, admin notes, and evidence export.
- The dashboard displays thumbnails but does not perform automated thumbnail image analysis.
- The dashboard includes basic visuals for concierge reports: retention curve, first-30-second comparison, baseline table, transcript timeline, and comment summary when available.
- Admin notes can be attached to evidence moments, baseline comparisons, preserve candidates, and experiment candidates.
- Admin notes remain internal by default and are labeled as admin-authored interpretation in exports.
- Evidence exports are admin-only, scoped to one analysis run, sanitized, and exclude tokens and unrelated channel data.
- A lightweight usage ledger tracks YouTube Data API calls, YouTube Analytics queries, transcript source, transcribed seconds, comment threads fetched, transcript chunks, embedded chunks, LLM usage if any, and retry/error counts.
- Artifact caching is allowed for metadata, transcripts, chunks, and comment samples. Fresh private analytics are fetched by default for refresh and retry unless cached data is explicitly chosen.
- Concierge reports are separate workflow objects tied to analysis runs.
- Concierge report fields include status, external draft URL, optional summary, feedback summary, creator feedback fields, creator delivery timestamps, author, and timestamps.
- Concierge report status is separate from analysis run status.
- Concierge statuses include evidence collected, in review, report drafted, sent to creator, feedback received, and closed.
- Concierge report drafts live in external docs first. No in-app rich editor is included in the first skeleton.
- Concierge feedback is captured manually in admin notes/feedback summary first.
- Report feedback captures usefulness, perceived alignment with YouTube Studio, style respect, whether it changed the creator's next decision, willingness to reuse/pay, and notable quotes.
- The frontend FAQ page explains why the product does not compare creators to big channels by default.
- The product principle is creator-native diagnosis over imitation-driven optimization.
- The product voice is an honest creator-side analyst with craft respect and evidence discipline.
- The report hierarchy is diagnosis, creator understanding, experiments, and optional rewrites.
- Learning mode exists for creators without enough baseline history. It shows evidence quality, not diagnosis confidence.
- Default comparison is the creator's own channel baseline. External references are future reference-not-benchmark inputs.
- Reports and future automated outputs include what to preserve, what to ignore, not recommended, less likely causes, metric priority, goal fit when relevant, audience-goal guidance when relevant, and creative tradeoffs for major experiments.
- Generated drafts and rewrites are optional learning aids, not "best" answers. They need separate fit/confidence labels.
- Full-script generation is not a default behavior and only happens after explicit user request in later chat functionality.
- Public URL analysis is not MVP diagnosis. Future public analysis should be labeled as a limited surface review.
- Teams, agencies, PDF exports, public share links, payment flows, and creator-facing report history are out of the first skeleton.

## Testing Decisions

- Good tests should verify externally observable behavior: API responses, persisted state, authorization gates, provider-wrapper calls, data deletion effects, run status transitions, and rendered UI behavior. Tests should not depend on private implementation details such as helper call order unless that behavior is part of a provider contract.
- Provider-mocked tests are required for Google OAuth/OIDC, YouTube Data API, YouTube Analytics API, transcript acquisition, Whisper fallback, and future comment fetching.
- Auth tests should cover OAuth state validation, ID token/user identity validation through the provider wrapper, granted-scope tracking, incomplete connection state, reconnect state, server-side session creation, logout, admin allowlist behavior, and CSRF protection on mutations.
- Token safety tests should verify refresh tokens are encrypted before storage, access tokens are not persisted by default, tokens are never returned to frontend APIs, and sanitized provider errors do not expose credentials.
- Authorization tests should verify users can only access their own channels, videos, runs, settings, and deletion actions; admin routes must reject non-admin users server-side.
- Multi-channel tests should cover one-channel auto-selection, multiple-channel picker state, active channel scoping, and analysis-run channel scoping.
- Video selection tests should verify owned-video listing, lightweight metadata rendering, ownership verification, Shorts exclusion, and no private analytics precomputation for every upload.
- Analysis-run tests should cover creation, queued/running/needs-input/completed/failed status transitions, step labels, linked retry, linked refresh, linked manual-context revision, and immutable prior runs.
- Migration tests should verify Alembic migrations create the expected schema and can run in a clean database.
- Baseline tests should cover recent-first candidate selection, backward expansion, first-7-day same-window comparison, exclusion reasons, outlier handling, duration mismatch handling, major-change manual exclusion, and manual admin overrides.
- Baseline quality tests should verify insufficient, limited, usable, and strong labels with reasons, plus report-type gating.
- Retention tests should cover raw retention storage, elapsed-ratio alignment, timestamp display, light smoothing, local drop detection, baseline delta detection, hook-window comparisons, retention-baseline quality tiers, and confidence downgrade when retention baseline coverage is limited.
- Transcript tests should cover YouTube transcript fast path, bounded retry behavior, Whisper fallback, manual transcript fallback, transcript source labeling, transcription caps, interval-level coverage, and retention-to-transcript mapping.
- Evidence-dashboard tests should verify admin-only access, selected video metadata display, thumbnail display without analysis claims, baseline included/excluded lists, retention visual data availability, transcript interval mapping, embedded player timestamp links, and admin notes persistence.
- Export tests should verify one-run scoping, inclusion of normalized evidence and admin notes, manual evidence labeling, and exclusion of tokens, raw OAuth payloads, and unrelated channel data.
- Usage-ledger tests should verify API call counts, analytics query counts, transcript source, transcribed seconds, comment fetch counts when implemented, chunk counts, embedding counts when implemented, retry counts, and error counts.
- Concierge workflow tests should verify separate concierge report objects, status transitions, external draft URL storage, feedback summary storage, and separation from analysis-run status.
- Data deletion tests should verify single-run deletion, all-analysis-data deletion, disconnect behavior, account deletion if implemented, and removal of associated transcript chunks, vectors when present, comments, manual evidence, feedback, admin notes, reports, and run artifacts.
- Frontend tests or type/build checks should cover creator connect/status/settings surfaces, admin run list/dashboard surfaces, and FAQ route rendering once frontend dependencies are available.
- Existing prior-art test patterns in the codebase include provider-mocked backend tests, API smoke tests with patched dependencies, status endpoint tests, prompt/citation validation tests, frontend typecheck/build checks, and `git diff --check` hygiene.
- The first skeleton should run focused tests after each implementation chunk, with full CI before a PR when practical.

## Out of Scope

- Full public automated diagnosis report generation.
- Creator-facing Coach LLM report prose.
- Public report UI beyond simple concierge status.
- Follow-up chat grounded in reports.
- Creator-facing report history.
- Payment, subscriptions, Stripe, or pricing flow.
- Team or agency workspace.
- PDF export, public share links, or client-facing report exports.
- Generic public URL diagnosis.
- Public "surface review" flow.
- Default competitor or big-channel comparison.
- External reference analysis except as future reference-not-benchmark direction.
- Automated thumbnail image analysis.
- Thumbnail generation.
- Caption-management scopes or private caption-file access.
- Revenue or monetization analytics.
- Shorts diagnosis.
- Durable job queue implementation.
- Full audit logging for admin evidence dashboard access.
- Persistent creator profile memory.
- Advice strictness selector.
- Implementation tracking for future experiments.
- Automated email notification for concierge report delivery.
- In-app rich text editor for report drafting.
- Full script generation as a default product behavior.

## Further Notes

The first skeleton exists to validate the product brain, not to automate it prematurely. The core risk is generic, overconfident, imitation-driven advice. The product should win by being honest, evidence-backed, creator-native, and careful about uncertainty.

Concierge validation should be run with 10-20 creators before investing deeply in automated diagnosis prose. A successful report is one that surfaces something YouTube Studio did not make clear, changes the creator's next experiment, respects the creator's taste, identifies at least one accurate preserve item, helps avoid overcorrection, and makes the creator want to use the product again.

The default product promise should be understanding and next experiments, not guaranteed causal certainty. A strong framing is: "Understand where your YouTube video lost momentum, what to preserve, and what to test next."

The product should avoid hostile or performative language. It should not use roast framing, "brutally honest" catchphrases, "the algorithm hated this," or shaming phrasing. It should sound like an honest creator-side analyst who understands YouTube feedback loops while respecting craft and taste.

Big-channel references should never be the default benchmark. If reference videos are added later, they should be treated as study material and analyzed for transferable mechanics, tradeoffs, and risks of imitation.
