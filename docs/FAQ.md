# Candor FAQ

This FAQ answers the questions most likely to come up while building or reviewing Candor, the OAuth-connected YouTube video diagnosis product.

## Questions

1. [What is Candor?](#1-what-is-candor)
2. [What question does Candor answer?](#2-what-question-does-candor-answer)
3. [Why does Candor need Google/YouTube OAuth?](#3-why-does-candor-need-googleyoutube-oauth)
4. [What data does Candor read?](#4-what-data-does-candor-read)
5. [What will Candor never do in MVP?](#5-what-will-candor-never-do-in-mvp)
6. [Why does Candor compare against the creator's own channel?](#6-why-does-candor-compare-against-the-creators-own-channel)
7. [Why does Candor avoid clickbait titles and thumbnail generation?](#7-why-does-candor-avoid-clickbait-titles-and-thumbnail-generation)
8. [What are the main pages in the app?](#8-what-are-the-main-pages-in-the-app)
9. [What happens after OAuth succeeds?](#9-what-happens-after-oauth-succeeds)
10. [Why is the app not a dashboard?](#10-why-is-the-app-not-a-dashboard)
11. [How does Candor choose videos for diagnosis?](#11-how-does-candor-choose-videos-for-diagnosis)
12. [Why are Shorts excluded in MVP?](#12-why-are-shorts-excluded-in-mvp)
13. [How does Candor handle too-new videos?](#13-how-does-candor-handle-too-new-videos)
14. [What is `waiting_for_data`?](#14-what-is-waiting_for_data)
15. [When does Candor send email?](#15-when-does-candor-send-email)
16. [What happens if required data never arrives?](#16-what-happens-if-required-data-never-arrives)
17. [What happens when transcript or comments are unavailable?](#17-what-happens-when-transcript-or-comments-are-unavailable)
18. [How does Candor decide whether evidence is sufficient?](#18-how-does-candor-decide-whether-evidence-is-sufficient)
19. [What does an insufficient-evidence report show?](#19-what-does-an-insufficient-evidence-report-show)
20. [How does Candor prevent made-up diagnoses?](#20-how-does-candor-prevent-made-up-diagnoses)
21. [What does follow-up chat do?](#21-what-does-follow-up-chat-do)
22. [How can a creator disconnect or delete data?](#22-how-can-a-creator-disconnect-or-delete-data)
23. [What visual direction should the frontend follow?](#23-what-visual-direction-should-the-frontend-follow)
24. [What is out of scope for MVP?](#24-what-is-out-of-scope-for-mvp)

## 1. What is Candor?

Candor is an OAuth-connected YouTube video performance diagnosis tool for serious creators. It analyzes one owned long-form video, compares it against the creator's own channel baseline, and produces an evidence-backed diagnosis report.

The product is report-first. Chat is secondary and stays attached to a generated report.

## 2. What question does Candor answer?

Candor answers:

```text
Why did this video underperform?
```

The answer should be direct, useful, and honest about evidence limits. Candor should feel like an experienced creator friend with receipts, not a gimmicky AI coach or a "brutally honest" roast.

## 3. Why does Candor need Google/YouTube OAuth?

Reliable diagnosis needs private creator analytics and ownership verification. Public metadata alone cannot reliably show retention, traffic, watch, engagement, subscriber, or same-window baseline signals.

OAuth also lets Candor verify that the selected video belongs to the connected creator before using private analytics.

## 4. What data does Candor read?

MVP uses narrow read-only scopes:

- Google identity: `openid`, `email`, and `profile`.
- YouTube read-only channel and video metadata.
- YouTube Analytics read-only performance metrics.

Candor stores only enough data to reproduce reports: selected video metadata, normalized analytics used in the report, baseline membership and metrics, retention points, transcript evidence, comment signals used as evidence, manual creator context, deterministic diagnosis JSON, report output, citations, and follow-up messages.

Candor does not continuously sync the whole channel in MVP.

## 5. What will Candor never do in MVP?

Candor will not:

- upload, edit, or delete videos;
- manage captions;
- request write/manage scopes;
- request revenue or monetary analytics scopes;
- expose OAuth tokens to the frontend;
- log OAuth credentials;
- continuously warehouse the creator's whole channel;
- claim knowledge of YouTube's internal recommendation model.

## 6. Why does Candor compare against the creator's own channel?

Candor is designed to understand the creator's own videos, audience, style, and baseline. Big creators often have different audiences, budgets, formats, publishing history, and distribution context. Using them as the default benchmark can push creators toward imitation instead of useful learning.

Reference videos may become future study material, but they should not replace the creator's own baseline.

## 7. Why does Candor avoid clickbait titles and thumbnail generation?

Candor is a diagnosis product, not a gimmick generator. It can suggest title directions or packaging follow-through when evidence supports that work, but it should not have a standalone title generator, thumbnail generator, viral ideas page, or copy-this-creator feature.

The product should help the creator understand what happened to their video, not push them to imitate someone else.

## 8. What are the main pages in the app?

Candor separates public, auth, and app responsibilities:

- `/` is the landing page with one promise, one report preview, and one `Connect YouTube` CTA.
- `/login` is the focused sign-in page.
- `/auth` is the focused Google/YouTube trust and permission detail page.
- `/app` is the authenticated workspace for video selection, analysis progress, reports, history, and settings.
- `/faq` is the supporting trust and education page.

Unauthenticated users who visit `/app` should go to `/login`. Connected users who visit `/auth` should continue to `/app`.

## 9. What happens after OAuth succeeds?

OAuth success routes to `/app`, not back to the landing page.

If one channel is available, the creator goes to video selection. If multiple channels are available, the app shows a compact active-channel picker first. If required scopes are missing, the user returns to `/auth` with a clear missing-access state.

## 10. Why is the app not a dashboard?

The product answers one question. A dashboard invites wandering before the creator gets value.

The authenticated app should open as a focused workflow:

1. Choose one owned long-form video.
2. Optionally add lightweight context.
3. Start diagnosis.
4. View report.

Secondary controls such as switch channel, settings, report history, raw evidence, export, and FAQ should be available but hidden behind menus or buttons.

## 11. How does Candor choose videos for diagnosis?

The user selects one owned upload manually. Candor should not precompute private analytics for every upload or auto-rank underperformers in MVP.

The upload UI should be a row list, not a card grid. Each row should show thumbnail, title, publish date, duration, public view count when available, one status label, and one `Diagnose` action.

A hidden URL-paste fallback can exist, but the backend must verify ownership before diagnosis.

## 12. Why are Shorts excluded in MVP?

Shorts behave differently enough that applying a long-form diagnostic model would be misleading. Candor should filter or disable Shorts and explain:

```text
Candor diagnoses long-form videos first. Shorts behave differently enough that this report would be misleading.
```

## 13. How does Candor handle too-new videos?

Candor uses clear age states:

- Under 72 hours: too new for a primary diagnosis.
- 72 hours to 7 completed days: early read with lower confidence.
- 7+ completed days: normal first-7-completed-days diagnosis window.

If required YouTube Analytics data is delayed or incomplete, the state is `waiting_for_data`, not `early_read`.

## 14. What is `waiting_for_data`?

`waiting_for_data` is a first-class run state for delayed required data. It is not a failure and not a request for user input.

Use it when required selected-video metadata, ownership/channel verification, authenticated YouTube Analytics, or baseline candidate data is unavailable or partially missing after bounded immediate retries.

Waiting runs store retry metadata such as `next_retry_at`, `retry_count`, and `last_data_wait_reason`. A lightweight scheduled backend check retries waiting runs and resumes analysis when required data is available.

## 15. When does Candor send email?

Candor sends transactional email only after explicit per-run consent.

In a `waiting_for_data` state, the UI can show `Notify me` if the user has a verified email and email is configured. After the user clicks it, Candor may email that verified Google email when the diagnosis is ready or when retry exhaustion fails the run.

Candor does not send automatic waiting-run email, newsletters, weekly reports, growth nudges, or reactivation emails.

The MVP email provider is Resend behind an email provider interface, with a fake provider for tests and local development.

## 16. What happens if required data never arrives?

After retry exhaustion, the run becomes terminal `failed` with a precise non-blaming reason:

```text
YouTube Analytics data was not available after several checks, so Candor could not produce a reliable diagnosis.
```

Candor preserves partial evidence internally for inspection, but it should not turn that partial evidence into a weak user report.

## 17. What happens when transcript or comments are unavailable?

Transcript and comments are supporting evidence, not always blocking evidence.

Candor retries transcript acquisition with a YouTube captions fast path and Groq Whisper fallback. If transcript still fails, the report can continue when core analytics and baseline data are available, but content-structure confidence is limited and the report can ask for a script or transcript.

Disabled, unavailable, sparse, or generic comments are neutral, not negative.

## 18. How does Candor decide whether evidence is sufficient?

A primary bottleneck can be named only when the run has:

- at least one authenticated analytics signal;
- at least 5 comparable prior long-form videos in the same-window channel baseline;
- at least one content or audience signal;
- one candidate bottleneck materially stronger than alternatives;
- at least one contradiction check;
- confidence tied to data completeness.

If that bar is not met, Candor should not name a confident primary bottleneck.

## 19. What does an insufficient-evidence report show?

Insufficient evidence is a first-class report state, not a failure.

It should show:

- no confident primary bottleneck;
- ranked hypotheses with low-confidence labels;
- missing evidence and why it matters;
- 1-3 targeted asks;
- a primary action such as `Add missing context`.

Thin channel history uses learning mode. With `0-2` comparable prior videos, there is no primary diagnosis. With `3-4`, Candor shows low-confidence ranked hypotheses.

## 20. How does Candor prevent made-up diagnoses?

Deterministic analyzers own metrics, baseline selection, retention mapping, candidate scoring, contradiction checks, evidence gates, and confidence. The LLM owns explanation and coaching only inside the deterministic evidence envelope.

Reports must use strict JSON and machine-readable citations to stored evidence. Invalid report JSON or invalid citations should be rejected before display. If LLM generation fails validation, Candor should use a deterministic fallback report.

## 21. What does follow-up chat do?

Follow-up chat is secondary and attached to the report. It answers questions about the stored analysis snapshot and cites report evidence.

It should not become a full-screen chatbot or a broad viral-title generator. Requests such as "give me 20 viral titles" should be refused or redirected unless grounded in the report and framed as learning from the creator's own evidence.

## 22. How can a creator disconnect or delete data?

Settings should include trust and account controls:

- connected Google identity;
- connected YouTube channel;
- granted access summary;
- disconnect YouTube;
- delete analysis data;
- FAQ/privacy links.

Disconnect removes or revokes future OAuth access where possible. Delete-analysis-data removes analysis runs, snapshots, reports, comments, manual evidence, follow-ups, and vectors. It should not automatically delete the user account unless a separate account-delete flow exists.

## 23. What visual direction should the frontend follow?

Candor should feel like a calm diagnostic workspace.

Design rules:

- red is only for errors;
- teal is a scarce truth accent;
- evidence blue is `#4B6B8C`;
- amber is for uncertainty, limitations, and missing data;
- use Inter for product UI and prose;
- use tabular numerals for all metrics;
- use mono only for timestamps, evidence IDs, raw metric labels, and compact diagnostic metadata.

Avoid purple AI gradients, neon growth-hacker colors, aggressive black/red styling, soft influencer pastels, decorative dashboard collages, and user-facing scores or grades.

## 24. What is out of scope for MVP?

Out of scope:

- public URL diagnosis without OAuth;
- diagnosing non-owned videos;
- Shorts diagnosis;
- automated thumbnail image analysis;
- standalone title or thumbnail generation;
- copying larger creators' style or format;
- pricing and billing UI;
- teams, agencies, and shared workspaces;
- marketing email;
- durable full queue infrastructure;
- continuous whole-channel sync;
- write/manage YouTube scopes;
- revenue analytics.
