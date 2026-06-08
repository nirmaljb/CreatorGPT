# PRD: Candor Multi-Page YouTube Diagnosis SaaS

## Problem Statement

Serious YouTube creators often know that a video underperformed, but they do not know why. YouTube Studio gives them metrics, but it does not turn those metrics into a clear, creator-specific diagnosis. The creator is left guessing whether the problem was packaging, hook, retention, topic-audience fit, engagement, distribution, timing, or missing context.

Most adjacent tools make the problem worse by offering clickbait titles, thumbnail gimmicks, generic AI coaching, imitation of large creators, fake certainty, or dashboards full of options. That does not help a creator understand their own channel, their own audience, or their own style.

Candor needs to answer one simple question:

"Why did my video not perform?"

The answer must be honest, evidence-backed, calm, and specific. Candor should feel like an experienced creator friend with receipts: direct and useful, but not theatrical, flattering, performatively brutal, or gimmicky. If the evidence is incomplete, Candor should say so and explain what is missing rather than inventing a confident diagnosis.

## Solution

Build Candor as a multi-page SaaS application for OAuth-connected YouTube video diagnosis.

The product separates public positioning, authentication, and the working app:

- `/` is a focused public landing page.
- `/login` is a focused sign-in page.
- `/auth` is a focused Google/YouTube trust and permission detail page.
- `/app` is the authenticated workspace where the creator selects one owned long-form upload and starts diagnosis.
- `/faq` is a supporting trust and education page.

The first implementation pass should build a polished static multi-page shell wired only to the current auth/session plumbing. The shell should establish the Candor brand, visual system, product hierarchy, and user flow without pretending missing backend slices already exist.

Candor's public promise is:

"Why did this video underperform?"

Supporting copy should explain that Candor connects to the creator's YouTube channel, compares one owned long-form video against that creator's own baseline, and gives the clearest diagnosis the evidence can support.

Candor should explicitly position itself against gimmicks:

- No clickbait titles.
- No thumbnail gimmicks.
- No copying bigger creators.
- No fake certainty.
- No generic AI coach.

The core flow is:

1. The creator lands on Candor and sees one clear CTA to connect YouTube.
2. The creator signs in on `/login` or reviews read-only access on `/auth` before continuing with Google.
3. After OAuth succeeds, the creator lands in `/app`.
4. If multiple channels are available, the creator chooses one active channel.
5. The creator selects one owned long-form video from a focused upload list.
6. The creator may optionally add lightweight context.
7. Candor starts diagnosis and shows honest evidence collection states.
8. If required analytics or baseline data is delayed, the run enters `waiting_for_data`.
9. The user can click `Notify me` for that run only.
10. Candor retries data collection durably and sends a transactional email only if the user requested it.
11. When complete, Candor shows a report, not a dashboard or chatbot.
12. Follow-up chat exists only as a secondary evidence-locked panel attached to the report.

## User Stories

1. As a serious YouTube creator, I want to understand why one video underperformed, so that I can make a better next video.
2. As a serious YouTube creator, I want the product to use my own channel baseline, so that the advice fits my audience and history.
3. As a serious YouTube creator, I want the product to avoid copying bigger creators, so that I can improve without losing my own style.
4. As a serious YouTube creator, I want a direct answer first, so that I do not have to inspect a dashboard before getting value.
5. As a serious YouTube creator, I want Candor to admit uncertainty, so that I can trust it when the evidence is incomplete.
6. As a serious YouTube creator, I want to connect YouTube with read-only access, so that Candor can use private analytics safely.
7. As a cautious creator, I want to know exactly what data Candor reads, so that I can decide whether OAuth access is acceptable.
8. As a cautious creator, I want to know what Candor will never do, so that I know it will not upload, edit, delete, manage captions, or read revenue metrics.
9. As a cautious creator, I want my refresh tokens kept off the browser, so that OAuth credentials are not exposed client-side.
10. As a creator arriving for the first time, I want a simple landing page, so that I immediately understand the product.
11. As a creator arriving for the first time, I want one primary CTA, so that I know the next step is connecting YouTube.
12. As a creator evaluating Candor, I want to see a report preview, so that I understand the shape of the diagnosis before connecting.
13. As a creator evaluating Candor, I want the preview to show what Candor does not know, so that I can see that uncertainty is part of the product.
14. As a creator evaluating Candor, I want the landing page to avoid feature overload, so that the product feels focused.
15. As a creator evaluating Candor, I want to see that Candor is not a clickbait title tool, so that I do not mistake it for a gimmick generator.
16. As a creator evaluating Candor, I want to see that Candor is not a thumbnail generator, so that I know it is a diagnosis product.
17. As a creator evaluating Candor, I want to see that Candor does not copy big creators, so that I know it respects my channel's style.
18. As a creator evaluating Candor, I want to see trust details in a footer or FAQ, so that the landing page stays simple.
19. As a creator signing in, I want the auth page to focus on permission clarity, so that I understand the consent request.
20. As a creator signing in, I want one `Continue with Google` action, so that the auth flow is obvious.
21. As a creator signing in, I want missing OAuth configuration or failed OAuth states explained safely, so that I understand what went wrong.
22. As an authenticated creator, I want successful OAuth to route me into the app, so that I can choose a video immediately.
23. As an authenticated creator, I want incomplete scopes to route me back to permission repair, so that diagnosis does not start without required access.
24. As an authenticated creator, I want the app to show my connected channel identity, so that I know which channel Candor will inspect.
25. As a creator with multiple YouTube channels, I want to switch the active channel, so that I can diagnose the right uploads.
26. As a creator with one active channel, I want the app to avoid workspace complexity, so that I can stay focused on one diagnosis.
27. As an authenticated creator, I want a focused upload list, so that I can choose one video quickly.
28. As an authenticated creator, I want uploads shown as rows rather than decorative cards, so that the list is easy to scan.
29. As an authenticated creator, I want each upload row to show title, thumbnail, publish date, duration, and public views when available, so that I can identify the video.
30. As an authenticated creator, I want each upload row to show a simple status label, so that I know whether it can be diagnosed.
31. As an authenticated creator, I want the default sort to be recent uploads, so that my likely candidate videos are easy to find.
32. As an authenticated creator, I want search and filters hidden behind a small control, so that the default interface is not crowded.
33. As an authenticated creator, I want a hidden URL-paste fallback, so that I can locate a video if upload search is imperfect.
34. As an authenticated creator, I want URL-pasted videos verified against my connected channel, so that Candor does not break the owned-video contract.
35. As an authenticated creator, I want non-owned videos rejected, so that private analytics are never implied for videos I do not own.
36. As an authenticated creator, I want Shorts excluded honestly, so that Candor does not apply long-form assumptions to a different format.
37. As an authenticated creator, I want Shorts to be filtered or disabled with a plain explanation, so that I know why they are unavailable.
38. As an authenticated creator, I want videos under 72 hours labeled too new, so that I understand why a primary diagnosis may be unreliable.
39. As an authenticated creator, I want videos from 72 hours to 7 completed days labeled as early reads, so that I understand the lower confidence.
40. As an authenticated creator, I want normal diagnosis to use the first 7 completed days by default, so that comparisons are consistent.
41. As a creator selecting a video, I want optional context chips, so that Candor can account for what felt wrong without forcing a questionnaire.
42. As a creator selecting a video, I want context to be optional, so that analysis can start without setup friction.
43. As a creator selecting a video, I want manual notes hidden behind `Add a note`, so that the default flow stays simple.
44. As a creator selecting a video, I want manual CTR, impressions, and retention context hidden behind `Add Studio metrics`, so that advanced inputs are available but not required.
45. As a creator adding context, I want manual evidence labeled as creator-provided, so that it is never confused with platform analytics.
46. As a creator starting analysis, I want the primary action to be `Start diagnosis`, so that I understand the next step.
47. As a creator waiting for analysis, I want to see evidence collection states, so that I know what Candor is checking.
48. As a creator waiting for analysis, I want states like waiting, checking, found, limited, and unavailable, so that progress is honest.
49. As a creator waiting for analysis, I want evidence rows for selected video snapshot, channel baseline, retention and analytics, transcript and structure, and comments and audience signals, so that I understand the report inputs.
50. As a creator waiting for analysis, I do not want fake percentages or dramatic AI loading copy, so that the product feels trustworthy.
51. As a creator waiting for analysis, I want missing required data handled differently from optional missing data, so that Candor does not give me a weak report when core evidence is unavailable.
52. As a creator waiting for analysis, I want delayed YouTube Analytics data to enter a waiting state, so that I know Candor is not done yet.
53. As a creator waiting for analysis, I want Candor to retry required analytics and baseline data, so that transient data delays can recover.
54. As a creator waiting for analysis, I want Candor to notify me only after I explicitly click `Notify me`, so that emails are consented per run.
55. As a creator waiting for analysis, I want `Notify me` to apply only to the current run, so that I am not opted into ongoing communication.
56. As a creator waiting for analysis, I want to see the target verified email before requesting notification, so that I know where the message will go.
57. As a creator waiting for analysis, I want no automatic email when I have not requested one, so that Candor respects my attention.
58. As a creator waiting for analysis, I want `Check again now`, so that I can manually retry when I return.
59. As a creator waiting for analysis, I want `Choose another video`, so that I can continue if one video's data is delayed.
60. As a creator whose required data never arrives, I want a precise terminal failure reason, so that I know Candor could not produce a reliable diagnosis.
61. As a creator whose required data never arrives, I want partial evidence preserved internally, so that the system can support debugging without showing a weak report.
62. As a creator whose required data never arrives, I want a failure email only if I requested notification, so that transaction emails stay consented.
63. As a creator whose transcript is unavailable, I want Candor to continue if core analytics and baseline data are available, so that optional evidence does not block the report.
64. As a creator whose comments are disabled or sparse, I want Candor to treat that as neutral, so that lack of comments is not treated as negative evidence.
65. As a creator whose manual metrics are missing, I want Candor to ask only when they materially improve confidence, so that I am not burdened with unnecessary inputs.
66. As a creator receiving a report, I want the top of the report to answer the main question, so that I do not have to hunt for the diagnosis.
67. As a creator receiving a report, I want to see the video title and thumbnail, so that I know which video was analyzed.
68. As a creator receiving a report, I want to see the likely bottleneck only when the evidence gate passes, so that Candor does not overclaim.
69. As a creator receiving a report, I want to see `No confident primary bottleneck yet` when evidence is insufficient, so that uncertainty is explicit.
70. As a creator receiving a report, I want confidence labels with reasons, so that I understand why the read is high, medium, low, or insufficient.
71. As a creator receiving a report, I do not want confidence percentages, so that the product avoids false precision.
72. As a creator receiving a report, I want an evidence quality strip, so that I can see which sources supported the report.
73. As a creator receiving a report, I want one short `what this means` paragraph, so that I can interpret the answer quickly.
74. As a creator receiving a report, I want one primary next action, so that I know what to do with the diagnosis.
75. As a creator receiving a report, I want detailed advice below the answer, so that the report hierarchy matches my intent.
76. As a creator receiving a report, I want rewrite suggestions only as diagnosis follow-through, so that Candor does not become a title generator.
77. As a creator receiving a report, I want title directions limited and evidence-based, so that they are useful without becoming clickbait.
78. As a creator receiving a report, I want packaging notes only when evidence supports them, so that Candor does not blame title or thumbnail without CTR or impression context.
79. As a creator receiving a report, I want Candor to say when the data does not support blaming packaging, so that I avoid fixing the wrong thing.
80. As a creator receiving a report, I want hook or retention diagnoses to cite retention evidence, so that they are not based on vibes.
81. As a creator receiving a report, I want engagement diagnoses to use opportunity-normalized metrics, so that raw counts do not mislead me.
82. As a creator receiving a report, I want distribution diagnoses to avoid algorithm certainty, so that Candor does not pretend to know YouTube's internal model.
83. As a creator receiving a report, I want compact raw evidence visible by default, so that the answer has receipts.
84. As a creator receiving a report, I want full raw evidence behind `View evidence`, so that I can inspect details without being overwhelmed.
85. As a creator receiving a report, I want baseline membership available in expanded evidence, so that I can trust the comparison set.
86. As a creator receiving a report, I want retention points available in expanded evidence, so that I can inspect timing.
87. As a creator receiving a report, I want comment samples available in expanded evidence when used, so that I can verify audience signals.
88. As a creator receiving a report, I want every factual claim traceable to stored evidence, so that the report is reproducible.
89. As a creator receiving an insufficient-evidence report, I want ranked hypotheses, so that I still get a useful read without fake certainty.
90. As a creator receiving an insufficient-evidence report, I want missing evidence listed with reasons, so that I know what would improve confidence.
91. As a creator receiving an insufficient-evidence report, I want 1-3 targeted asks, so that I can add only useful context.
92. As a creator receiving an insufficient-evidence report, I want `Add missing context` as the main action, so that the path forward is clear.
93. As a creator with few prior videos, I want learning mode instead of a confident diagnosis, so that thin history does not produce a fake conclusion.
94. As a creator with 0-2 comparable videos, I want no primary diagnosis, so that Candor respects baseline limits.
95. As a creator with 3-4 comparable videos, I want low-confidence hypotheses only, so that I can still learn carefully.
96. As a creator with 5 or more comparable videos, I want Candor to allow a stronger baseline gate when other evidence also passes, so that mature channels get more decisive reports.
97. As a creator using follow-up chat, I want it attached to the report, so that answers stay grounded.
98. As a creator using follow-up chat, I want it visually secondary, so that the report remains the product.
99. As a creator using follow-up chat, I want broad viral-title requests redirected or refused unless grounded in the report, so that Candor does not become a gimmick tool.
100. As a creator adding context after a report, I want a new linked revision report, so that the original report remains unchanged.
101. As a creator adding context after a report, I want the revised report labeled as revised with creator context, so that lineage is clear.
102. As a creator refreshing analytics, I want a linked refresh run, so that older reports remain reproducible.
103. As a creator retrying failed analysis, I want a new linked run, so that failure records are not mutated.
104. As a creator viewing history, I want previous reports available in low-prominence UI, so that trust history exists without distracting from the main workflow.
105. As a creator viewing history, I want each item to show title, run date, final state, confidence, bottleneck, and run reason, so that I can distinguish original, retry, refresh, and revision reports.
106. As a creator using settings, I want connected Google identity and YouTube channel information, so that I understand account state.
107. As a creator using settings, I want granted access summarized, so that I can verify the trust boundary.
108. As a creator using settings, I want to disconnect YouTube, so that I can revoke or remove future access.
109. As a creator using settings, I want to delete analysis data, so that I can remove stored reports and evidence.
110. As a creator deleting data, I want confirmation copy to say exactly what is deleted and what remains, so that the action is clear.
111. As a creator using settings, I do not want theme, coaching style, provider, workspace, or team preferences, so that settings stay focused on trust and recovery.
112. As a creator reading FAQ, I want to know why Candor needs OAuth, so that I understand why public data is insufficient.
113. As a creator reading FAQ, I want to know what data Candor reads, so that the trust model is transparent.
114. As a creator reading FAQ, I want to know what Candor never does, so that I understand safety boundaries.
115. As a creator reading FAQ, I want to know why Candor compares against my channel instead of big creators, so that I understand the anti-imitation stance.
116. As a creator reading FAQ, I want to know why Candor may say `we do not know yet`, so that I trust honest uncertainty.
117. As a creator reading FAQ, I want to know why Shorts are excluded, so that long-form assumptions are not surprising.
118. As a creator reading FAQ, I want to know why Candor does not generate clickbait titles or thumbnails, so that product boundaries are clear.
119. As a creator reading FAQ, I want to know how to disconnect and delete data, so that I feel in control.
120. As an internal operator, I want a separate admin evidence view, so that I can validate runs during concierge MVP operation.
121. As an internal operator, I want admin tooling hidden from normal creators, so that the creator experience stays focused.
122. As an internal operator, I want to inspect evidence availability, retry state, failure reasons, and manual notes, so that I can debug reports.
123. As an internal operator, I never want raw OAuth tokens shown, so that admin tooling does not create credential risk.
124. As a developer, I want a small durable retry mechanism for waiting runs, so that delayed data survives app restarts without a full queue.
125. As a developer, I want retry metadata stored on runs, so that data waiting is inspectable and testable.
126. As a developer, I want an email provider interface, so that transactional email can be mocked and swapped.
127. As a developer, I want Resend as the first real email provider, so that MVP transactional email stays simple.
128. As a developer, I want a fake email provider for local and test environments, so that tests do not call external services.
129. As a developer, I want no marketing email flows, so that the notification system stays transactional.
130. As a developer, I want strict report JSON and citation validation, so that LLM prose cannot invent final diagnoses.
131. As a developer, I want deterministic fallback output, so that report display remains safe when LLM report generation fails.
132. As a developer, I want provider-mocked tests, so that CI does not require real Google, YouTube, Groq, Qdrant Cloud, Neon, or Resend access.
133. As a developer, I want visual routes separated early, so that landing, auth, and app responsibilities do not blend.
134. As a developer, I want the first frontend chunk wired only to current session/OAuth plumbing, so that the product shell can land before backend slices are ready.
135. As a developer, I want hidden controls for secondary options, so that the app does not become a control panel.
136. As a developer, I want no billing or pricing UI in MVP, so that validation stays focused on diagnosis quality.
137. As a developer, I want no team workspace implementation in MVP, so that permission scope stays small.
138. As a developer, I want no public URL diagnosis in MVP, so that the OAuth-owned-video contract remains intact.
139. As a developer, I want current legacy comparison surfaces retired or isolated, so that old product behavior does not confuse the pivot.
140. As a developer, I want all new product behavior to target `analysis_run`, so that legacy sessions do not drive the new app.

## Implementation Decisions

- The user-facing product name is Candor.
- Candor means frank, unvarnished honesty and should position the brand against AI slop before the user reads a feature list.
- The public landing page should use the headline `Why did this video underperform?`.
- The public landing page should have one primary CTA: `Connect YouTube`.
- The public `Connect YouTube` CTA should route to `/login`.
- `/login` should be a focused sign-in page, not a second permission explainer.
- The public landing page should contain five tight sections: hero, report preview, how it works, what Candor is not, and trust footer.
- The landing page should not include pricing, testimonials, broad feature grids, blog links, or secondary product modes in MVP.
- The landing page should use one focused report-preview artifact rather than stock imagery, abstract AI visuals, or a dashboard collage.
- The report preview should use a hook/expectation example rather than packaging as the example bottleneck.
- The report preview should explicitly show what Candor knows and what it does not know yet.
- `/auth` should be a trust-and-consent page, not a second landing page.
- `/auth` should show one primary `Continue with Google` CTA.
- `/auth` should summarize Google identity, YouTube channel/video access, and YouTube Analytics access.
- `/auth` should clearly state that Candor will not upload, edit, delete, manage captions, read revenue metrics, expose tokens to the browser, or continuously sync the whole channel.
- If YouTube data is delayed, email notification should be mentioned only in auth/trust copy and delayed-run UI, not on the landing page.
- OAuth success should route to `/app`, not back to `/`.
- OAuth with incomplete scopes should route to `/auth` with a missing-access state.
- The authenticated app should open as a focused video-selection workflow, not a general analytics dashboard.
- The app should use minimal top navigation with the Candor brand, the current workflow label, and a channel/account chip.
- MVP should not include a permanent sidebar.
- Switch channel, report history, settings, disconnect, delete data, and FAQ should live behind secondary controls or the account menu.
- The upload selector should be a focused row list rather than a card grid.
- Upload rows should show a small thumbnail, title, publish date, duration, public view count when available, one status label, and one primary `Diagnose` action.
- Search and filters should be hidden behind a small `Filter` button.
- The default upload sort should be recent uploads.
- URL paste should exist only as a hidden fallback and must verify that the video belongs to the connected channel.
- Candor should diagnose long-form uploads only in MVP.
- Shorts should be filtered or disabled with a quiet explanation and should not produce a long-form diagnosis.
- Videos under 72 hours should be marked too new for a primary diagnosis.
- Videos from 72 hours to 7 completed days should be marked as early reads.
- Videos with at least 7 completed days should use the normal first-7-completed-days diagnosis window.
- Optional pre-analysis context should be lightweight and should not block analysis.
- Pre-analysis context should include simple `What felt wrong?` chips and hidden optional note/manual metrics controls.
- Manual context should be structured-first, optional, and visibly labeled as creator-provided.
- Adding manual context that changes interpretation should create a linked revision run, not mutate the original report.
- Refreshing analytics should create a linked refresh run.
- Retrying a failed analysis should create a linked retry run.
- Analysis progress should show honest evidence collection states, not fake percentage loaders.
- Evidence collection rows should include selected video snapshot, channel baseline, retention and analytics, transcript and structure, and comments and audience signals.
- Core diagnosis data should block final report generation when unavailable after bounded immediate retries.
- Core blocking data includes authenticated YouTube Analytics signals, baseline candidate data, selected video metadata, and required ownership/channel verification.
- Non-blocking evidence after bounded retries includes transcript, comments, optional manual context, optional CTR, and optional impression metrics.
- Required analytics or baseline delays should use a first-class `waiting_for_data` run state.
- `waiting_for_data` should be distinct from failure and from `needs_input`.
- Waiting runs should store retry metadata including next retry time, retry count, and the latest wait reason.
- A lightweight durable retry job should resume waiting runs when required data becomes available.
- A full durable queue such as Celery or Redis is out of scope for this MVP slice.
- If required data remains unavailable after retry exhaustion, the run should become terminal `failed` with a precise non-blaming explanation.
- Partial evidence from failed runs should remain internally inspectable but should not become a weak user report.
- Transactional email should use Resend behind an email provider interface.
- Local and test environments should use a fake email provider.
- Email notifications should be transactional only.
- The app should send diagnosis-ready-after-waiting and exhausted-retry-failure emails only when the user explicitly requested notification for that run.
- `Notify me` should require an explicit click and should apply per run only.
- Candor should not create account-wide email preferences in MVP.
- If email is missing, unverified, or the provider is not configured, Candor should show a check-later state and should not pretend notification will happen.
- The completed user-facing artifact should be called a report.
- The report first screen should prioritize answer, confidence, and evidence quality before advice.
- The report should show a primary bottleneck only when the evidence gate passes.
- If the evidence gate does not pass, the report should show `No confident primary bottleneck yet`.
- Insufficient evidence should be a first-class report state, not a product failure.
- Insufficient-evidence reports should show ranked hypotheses, missing evidence, 1-3 targeted asks, and `Add missing context`.
- Thin channel history should enter learning mode, not diagnosis mode.
- Fewer than 5 comparable prior long-form videos should prevent a confident primary bottleneck.
- Confidence should be shown as high, medium, low, or insufficient evidence, always with a reason.
- Candor should not show confidence percentages or overall performance scores.
- Candor should not show virality scores, thumbnail scores, hook scores, or video grades.
- Raw metrics should appear as a compact evidence strip by default, with full details behind `View evidence`.
- Charts should be sparse and takeaway-led.
- The report may use one retention-vs-baseline line chart when retention data is available.
- The report may use small baseline comparison bars for a few key metrics.
- Every chart should have a plain-language takeaway.
- Title and packaging rewrites should be included only as report follow-through, not as a standalone generator.
- Packaging cannot be high confidence without CTR/impression context or equivalent click-opportunity evidence.
- Automated thumbnail image analysis is out of scope for MVP.
- Follow-up chat should be present but visually secondary and locked to the stored report snapshot.
- Follow-up chat should not answer broad viral-title or creator-copying requests unless grounded in the report and reframed as learning.
- Report history should exist but remain low prominence.
- Creator settings should include trust and account controls only.
- Settings should include connected identity, active channel, granted access, disconnect, delete analysis data, and FAQ/privacy links.
- Settings should not include theme controls, coaching style controls, model/provider controls, team settings, or workspace preferences.
- Disconnect YouTube should remove or revoke future OAuth access where possible without automatically deleting prior reports.
- Delete analysis data should delete analysis runs, snapshots, reports, comments, manual evidence, follow-ups, and vectors.
- Admin evidence tooling should be separate from normal creator UX and visible only to internal or allowlisted users.
- Admin tooling should support run inspection, evidence availability, statuses, retry state, failure reasons, and manual notes.
- Admin tooling must never expose tokens or raw OAuth credentials.
- The visual system should communicate calm evidence rather than harsh critique.
- Red should be reserved for errors and should not be a primary brand color.
- Teal should be a scarce truth accent, not a surface color.
- Evidence blue should use `#4B6B8C`.
- Amber should be reserved for uncertainty, limitations, and missing data.
- Typography is load-bearing for trust.
- Product UI and prose should use Inter with system sans fallback.
- Metrics should use tabular numerals.
- Timestamps, evidence IDs, raw metric labels, and compact diagnostic metadata should use a mono face.
- The core app should avoid serif headlines.
- Every number in reports, cards, tables, charts, progress states, and baseline comparisons should use tabular numerals.
- The product voice should be specific, evidence-bound, and non-performative.
- Candor should avoid phrasing like `brutally honest`, `the algorithm killed it`, or `your hook was bad`.
- Candor should use careful language such as `likely`, `suggests`, and `based on available evidence`.
- The first frontend implementation pass should build the polished static multi-page shell wired to current `/me` and OAuth start behavior.
- Real video listing, report generation, admin dashboard, delayed retry, email implementation, and settings deletion flows can follow in later slices.
- After the static shell, implementation priority should be auth route split and redirects, channel selection, owned upload list, create analysis run, waiting-for-data retry metadata, transactional email provider, report shell, settings controls, and admin evidence dashboard.

## Testing Decisions

- Tests should verify externally observable behavior rather than implementation details.
- Frontend tests should verify route responsibility: landing page, auth page, app shell, and FAQ page each show the correct primary action and trust copy.
- Frontend tests should verify connected, disconnected, incomplete-scope, and reconnect-required session states using mocked session payloads.
- Frontend tests should verify unauthenticated app access routes the user toward authentication.
- Frontend tests should verify connected auth access routes the user toward the app.
- Frontend tests should verify the upload list model with ready, too-new, early-read, Short-not-supported, provider-error, and empty states.
- Frontend tests should verify that secondary options remain hidden behind menus or buttons.
- Frontend tests should verify the `waiting_for_data` state shows `Notify me`, `Check again now`, and `Choose another video`.
- Frontend tests should verify notification copy only appears when the user can explicitly request it.
- Frontend tests should verify report hierarchy: answer, confidence reason, evidence quality, then advice.
- Frontend tests should verify insufficient-evidence reports show hypotheses and missing context prompts instead of a confident diagnosis.
- Frontend tests should verify no user-facing score or confidence percentage is rendered.
- Backend tests should mock Google OAuth and YouTube providers.
- Backend tests should verify OAuth scopes, missing-scope behavior, session payload shape, and safe redirect handling.
- Backend tests should verify YouTube channel selection and ownership checks.
- Backend tests should verify Shorts detection prevents diagnosis creation.
- Backend tests should verify age-state classification for under-72-hour, early-read, and normal-window videos.
- Backend tests should verify analysis run creation, status transitions, retry linkage, refresh linkage, and manual-context revision linkage.
- Backend tests should verify `waiting_for_data` is used only for delayed required data, not optional transcript/comment absence.
- Backend tests should verify retry metadata updates without mutating old run evidence.
- Backend tests should verify retry exhaustion becomes failed with a precise reason.
- Backend tests should verify per-run notification consent is required before sending diagnosis-ready or failure emails.
- Backend tests should verify fake email provider behavior without calling external services.
- Backend tests should verify Resend provider requests through a provider abstraction rather than direct app calls.
- Backend tests should verify delete-analysis-data removes reports, snapshots, comments, manual evidence, follow-ups, vectors, and usage rows while preserving or separately handling the user account according to the final deletion contract.
- Diagnosis engine tests should verify evidence gates, confidence labels, contradiction checks, thin-history learning mode, packaging confidence caps, retention requirements, and deterministic fallback behavior.
- Report validation tests should verify strict JSON shape and machine-readable citations before display.
- Follow-up chat tests should verify responses are grounded in stored report snapshots and reject unsupported broad requests.
- Admin tests should verify authorization boundaries and ensure normal users cannot access internal evidence views.
- Existing provider-mocked tests for OAuth, structured errors, backpressure, mocked smoke, and frontend lint/typecheck provide useful prior art.
- CI should not require real Google, YouTube, Groq, Qdrant Cloud, Neon, or Resend credentials.
- Visual verification should be performed for the frontend shell after implementation, including desktop and mobile viewports, to catch text overflow and layout overlap.

## Out of Scope

- Public YouTube URL diagnosis without OAuth.
- Diagnosing videos not owned by the connected channel.
- Shorts diagnosis.
- Automatic thumbnail image analysis.
- Standalone title generator.
- Standalone thumbnail generator.
- Viral title generator.
- Copying large creators' formats, titles, thumbnails, or personal styles.
- Pricing, billing, plan limits, or paywall UI.
- Team workspaces, agency dashboards, invites, roles, and approval workflows.
- Marketing newsletters, weekly reports, reactivation emails, and growth nudges.
- Durable full queue infrastructure such as Celery, Redis workers, or a managed task queue in the first MVP slice.
- Continuous whole-channel analytics sync.
- Revenue or monetary analytics scopes.
- Write/manage YouTube scopes.
- Caption management scopes.
- Automated ranking of all uploads by opportunity.
- User-facing analytics dashboard as the app home.
- User-facing numeric scores or grades.
- Theme settings, coaching-style settings, and model/provider settings.
- Replacing YouTube Studio.
- Claiming knowledge of YouTube's internal recommendation algorithm.

## Further Notes

- Current repo state includes a basic Google OAuth/session foundation, a frontend OAuth start proxy, a same-origin session proxy, and a connection-oriented home page plus FAQ.
- The current frontend still uses the older `Signal Room` label and should be renamed to Candor during the shell implementation.
- The current app route shape does not yet match the accepted split of landing, auth, and authenticated app.
- The codebase still contains legacy two-video comparison and session-oriented concepts that should be isolated or retired as the pivot progresses.
- The prior `issues/` directory was not present at the time this PRD was written, so this file recreates the local PRD entry point.
- Existing progress notes mention earlier vertical-slice issues, but this PRD supersedes the missing local issue files for the Candor multi-page SaaS/frontend-and-flow plan.
- The PRD intentionally captures accepted product decisions from the grilling session before implementation starts.

## Implementation Notes

- 2026-06-08: Implemented the first AFK frontend shell slice. `/` is now the public Candor landing page, `/auth` owns Google/YouTube permission and OAuth-unavailable states, `/app` is a guarded workspace shell wired to current `/api/me`, and `/faq` is expanded for trust and education. The PRD remains open because channel selection, owned uploads, analysis runs, waiting-data retry, notifications, reports, settings, and admin evidence tooling remain unimplemented.
- 2026-06-08: Added `/login` as the separate sign-in page. Public CTAs now route to `/login`, `/auth` remains the permission-detail page, OAuth-start failures return to the initiating login/auth page, and successful OAuth callback redirects to `/app`.
- Verification: `npm run typecheck`, `npm run lint`, `npm run build`, and `git diff --check` passed. `npm run build` now lists `/`, `/auth`, `/app`, and `/faq`. Visual browser verification could not run because the sandbox rejected local server binding with `EPERM` and the in-app Browser `iab` instance was unavailable.
