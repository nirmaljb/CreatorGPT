# Product Spec: Candor YouTube Video Performance Diagnosis

## 1. Product Summary

We are building Candor, an AI-assisted analytics product that helps serious YouTube creators understand why a video underperformed and what they should change in the next upload.

The product is a structured video post-mortem system, not a generic "chat with video" tool.

A creator connects their YouTube account, selects one owned video that performed worse than expected, and receives an evidence-backed diagnosis report. The system analyzes authenticated YouTube analytics, channel baseline performance, transcript structure, comments, title, thumbnail, description, and available public metadata. It then identifies the most likely bottleneck or explicitly says that the data is insufficient to name one.

The goal is to move the creator from:

```text
This video flopped. I do not know why.
```

to:

```text
This video likely failed at the hook or retention stage. Here is the evidence, here is the uncertainty, and here is what to change next time.
```

## 2. Positioning

Primary positioning:

```text
Candor answers "Why did this video underperform?" with creator-owned evidence.
```

Alternative positioning:

- Frank, evidence-backed YouTube video diagnosis.
- Turn failed YouTube videos into better next uploads.
- Understand why your YouTube video underperformed.
- Find where your video lost viewers and what to fix next.
- YouTube post-mortems that admit what the evidence can and cannot support.

This product is not:

- a YouTube SEO tool;
- a keyword research tool;
- a generic chatbot;
- a generic AI coach;
- a clickbait title generator;
- a thumbnail generator;
- a tool for copying large creators' videos, formats, thumbnails, titles, or personal style;
- a replacement for YouTube Studio;
- a tool that claims to know YouTube's internal algorithm.

The product voice should feel like an experienced creator friend who is careful with the evidence: direct, useful, and honest about what it understands. It should not flatter the creator, market "brutally honest" takedowns, or give gimmicky answers. The product studies the creator's own channel, their own video style, and their own audience patterns, then explains what likely happened and what to try next.

Landing-page positioning should stay focused on one promise: answer "Why did my video not perform?" with creator-owned evidence. The primary call to action is connecting YouTube. Supporting copy should explain read-only access, channel-relative baseline comparison, and the anti-imitation stance without presenting many competing options.

Initial landing copy direction:

- Headline: `Why did this video underperform?`
- Subheadline: `Candor connects to your YouTube channel, compares one owned long-form video against your own baseline, and gives you the clearest diagnosis the evidence can support.`
- CTA: `Connect YouTube`
- Anti-gimmick line: `No clickbait titles. No thumbnail gimmicks. No copying bigger creators. Just a careful read on your video, your audience, and what to try next.`

## 2.1 Product Experience And Visual System

Candor is a multi-page SaaS application with clear route responsibilities:

- `/` is a focused public landing page.
- `/login` is a focused sign-in page with one Google OAuth action.
- `/auth` is a Google/YouTube trust and permission detail page.
- `/app` is the authenticated workspace for video selection and diagnosis.
- `/faq` is a supporting trust and education page.

The landing page should use five tight sections:

1. Hero with the promise and one `Connect YouTube` CTA.
2. One focused report preview artifact.
3. How it works: connect, choose one video, get the diagnosis.
4. What Candor is not: no clickbait titles, thumbnail gimmicks, copying big creators, or fake certainty.
5. Trust footer: read-only access, no revenue metrics, disconnect/delete data.

The landing page should not include pricing, testimonials, broad feature grids, dashboards, blog links, or secondary product modes in MVP.

The visual system should feel like calm evidence:

- Graphite or near-black for seriousness.
- Clean off-white and light neutrals for breathing room.
- Teal as a scarce truth accent, not a dominant surface color.
- Evidence blue `#4B6B8C` for analytics and report evidence.
- Amber for uncertainty, limitations, and missing data.
- Red only for errors, never as the brand color.

Typography is part of the trust system:

- Use Inter for product UI and prose with system sans fallback.
- Use tabular numerals for all metrics, report numbers, progress states, tables, charts, and baseline comparisons.
- Use a mono face for timestamps, evidence IDs, raw metric labels, and compact diagnostic metadata.
- Avoid serif headlines in the core app.

Candor should not show user-facing scores, video grades, virality scores, hook scores, thumbnail scores, or confidence percentages.

## 3. Target Customer

Primary users are serious YouTube creators who post consistently and already care about performance.

They understand or are actively learning terms such as:

- CTR;
- impressions;
- retention;
- average view duration;
- watch time;
- hooks;
- thumbnails;
- audience engagement;
- traffic sources.

Secondary users:

- YouTube editors;
- scriptwriters;
- creator managers;
- creator agencies;
- content strategists;
- small media teams;
- brand content teams running YouTube channels.

Not ideal for the MVP:

- beginner creators with too few videos for a meaningful baseline;
- casual uploaders;
- users who only want viral title ideas;
- creators unwilling to connect YouTube;
- creators with no meaningful performance history.

## 4. Core Pain

YouTube Studio shows metrics, but creators still struggle to interpret what those metrics mean.

Creators ask:

- Why did this video suddenly stop getting impressions?
- Why did this video flop even though some metrics looked fine?
- Was the issue title, thumbnail, topic, hook, pacing, audience fit, or satisfaction?
- What should I change in my next video?
- Which metrics should I ignore?
- What did stronger videos on my own channel do differently?

The product turns raw analytics into clear creative and strategic decisions.

## 5. Core Promise

Given one underperforming YouTube video owned by the authenticated creator, the system will:

1. Build a channel-relative performance baseline.
2. Analyze where the video likely lost momentum.
3. Explain the evidence and limitations behind the diagnosis.
4. Compare the video against comparable prior uploads.
5. Generate a practical next-video improvement plan.
6. Ask for missing context only when the data is insufficient for a reliable conclusion.

## 5.1 MVP Product Contract

The MVP contract is OAuth-first, owned-video, and long-form-only.

- The user must connect YouTube before receiving the core diagnosis experience.
- The selected video must belong to the authenticated channel.
- Shorts are detected and excluded from MVP diagnosis.
- Public URL analysis can become a future low-confidence/free path, but it does not define the MVP.
- The default comparison window is the first 7 completed days after publish.
- Videos between 72 hours and 7 days old can receive an early-read report with lower confidence.
- Videos under 72 hours old can create a snapshot, but should not receive a primary bottleneck unless signals are unusually strong.
- The system baseline defines underperformance by default. Creator expectations are optional context and must be stored separately from platform evidence.

## 6. MVP Workflow

### Step 0: Route Into The Right Page

The public site, authentication, and working app should remain separate:

- unauthenticated users who visit `/app` should be routed to `/login`;
- the public `Connect YouTube` CTA should route to `/login`;
- connected users who visit `/auth` should continue to `/app`;
- successful OAuth should route to `/app`, not back to `/`;
- incomplete scopes should route to `/auth` with a clear missing-access state.

### Step 1: Connect YouTube

The user signs in with Google and grants read-only YouTube and YouTube Analytics access.

MVP scopes:

- `openid`
- `email`
- `profile`
- `https://www.googleapis.com/auth/youtube.readonly`
- `https://www.googleapis.com/auth/yt-analytics.readonly`

### Step 2: Select A Video

The app lists owned videos from the connected channel. The user selects one video to diagnose. The authenticated app should open as a focused video-selection workflow, not a dashboard.

The upload selector should be a row list, not a decorative card grid. Each row should show a small thumbnail, title, publish date, duration, public view count when available, one status label, and one primary `Diagnose` action. Search and filters should be hidden behind a small control. Default sort is recent uploads.

Pasting a URL can be supported as a hidden fallback, but the backend must verify that the video belongs to the authenticated channel before using private analytics.

MVP does not automatically rank or detect underperforming videos across the channel. The upload list can show lightweight metadata such as title, thumbnail, publish date, duration, and public views, but private analytics should be fetched only after the user selects one video and only for the selected run and its baseline candidates.

If the authenticated Google account has multiple YouTube channels or brand accounts, the app should support a one-active-channel picker. The schema must support multiple channels per user, but team and multi-channel workspace flows are not MVP.

If the selected video is a Short, the MVP should show that Shorts diagnosis is not supported yet rather than forcing a long-form diagnostic model onto it. Suggested copy: `Candor diagnoses long-form videos first. Shorts behave differently enough that this report would be misleading.`

### Step 3: Analyze First

The system analyzes before asking the creator to answer setup questions.

It fetches and stores an analysis snapshot:

- video metadata;
- transcript or Whisper transcript;
- comments and timestamped reactions;
- private analytics available through YouTube Analytics;
- channel baseline videos;
- retention curve;
- traffic, watch, engagement, subscriber, and trend signals;
- title, thumbnail, description, and packaging signals.

The system may show an optional "what felt wrong?" selector, but it must not block analysis. Suggested chips are `Low views`, `Weak retention`, `Good comments but low reach`, `Wrong audience`, and `Not sure`. Optional notes, manual CTR, impressions, and retention context should be hidden behind secondary controls.

Required questions should appear only when the evidence gate fails or a specific manual input would materially improve confidence.

### Step 4: Wait For Required Data When Needed

If selected-video metadata, ownership/channel verification, authenticated YouTube Analytics signals, or baseline candidate data is unavailable or partially missing, Candor should retry rather than produce a weak limited report.

After bounded immediate retries, runs that are waiting on required data should enter `waiting_for_data`. This is not `failed` and not `needs_input`; no user action is required. The UI should say:

```text
Candor is waiting for YouTube Analytics data to settle. We will email you when the diagnosis is ready if you ask us to notify you.
```

`Notify me` is explicit and per-run only. Candor must not send automatic waiting-run email unless the user clicks `Notify me`. If email is missing, unverified, or not configured, show `Check again later` rather than pretending notification will happen.

Transcript, comments, optional manual context, optional CTR, and optional impressions are non-blocking after bounded retries. They should be labeled unavailable or limited and can trigger targeted asks, but they should not keep a run waiting forever when core analytics and baseline data are available.

If required data remains unavailable after retry exhaustion, the run becomes terminal `failed` with a precise, non-blaming explanation. It must not become a weak report.

### Step 5: Evidence Gate

The deterministic diagnosis engine decides whether evidence is sufficient to name a primary bottleneck.

The report can name a primary bottleneck only when there is:

- at least one authenticated analytics signal;
- at least 5 comparable prior long-form videos in a same-window channel-baseline comparison;
- at least one content or audience signal;
- one candidate bottleneck that scores materially stronger than alternatives;
- at least one contradiction check showing why another plausible bottleneck is less likely;
- a confidence level tied to data completeness.

If fewer than 5 comparable prior long-form videos are available, the app may still create an analysis run, but it must not produce a confident primary bottleneck:

- `0-2` comparable prior videos: no primary diagnosis; show missing baseline and ask for manual references or more history.
- `3-4` comparable prior videos: ranked hypotheses only, low confidence, and explicit limitations.
- `5+` comparable prior videos: the baseline gate can pass if the other gates pass.

### Step 6: Generate Report

The report appears automatically when analysis completes. Chat unlocks after the report exists.

If an analysis run fails, the user can retry analysis. Retry creates a new `analysis_run` linked to the failed run rather than mutating the old run. Refresh and manual-context revisions also create linked runs. This preserves immutable snapshots, reports, citations, feedback, and failure records while allowing safe artifact reuse.

### Step 7: Ask Only If Needed

If data is insufficient, the product asks 1-3 targeted questions or requests specific manual metrics. It should explain what each missing answer would unlock.

Examples:

- "Enter CTR and impressions from YouTube Studio to strengthen packaging diagnosis."
- "Do you have a script or transcript you want to add?"
- "Was this expected to perform like your recent uploads or like a specific reference video?"
- "Was the intended audience your existing subscribers or a new segment?"

## 7. Diagnosis Framework

Every diagnosis follows:

```text
Signal -> Evidence -> Interpretation -> Confidence -> Action
```

Example:

```text
Signal:
First-30-second retention is meaningfully below the channel baseline while title and topic performance are not clearly below baseline.

Evidence:
The selected video loses viewers earlier than comparable uploads, and the transcript delays the main promise until after the setup.

Interpretation:
The click may not be the main failure. The opening likely did not satisfy the expectation quickly enough.

Confidence:
Medium-high because retention and transcript signals agree, but CTR/impressions are not available through API data.

Action:
Open the next video with the result, conflict, or stakes before background context.
```

## 8. Failure Types

### Packaging Failure

The video failed before enough viewers clicked.

Possible signals:

- low views or weak distribution vs baseline;
- low manual CTR if user provides it;
- title lacks clear promise;
- thumbnail/title concern manually provided by the creator;
- similar channel videos with clearer packaging performed better.

Constraint:

Do not claim API-backed CTR or impressions unless they are actually available. CTR and impressions are optional/manual MVP inputs, not mandatory platform signals.

Without CTR or impression context, packaging can be a hypothesis or secondary concern, but it cannot be a high-confidence primary diagnosis. Title and thumbnail critique can support "the promise may be unclear," but not "this is why the video failed before the click" unless click-opportunity evidence exists.

MVP does not include automated thumbnail image analysis. Store and display the thumbnail, but do not claim visual readability, hierarchy, emotional clarity, or title-thumbnail alignment unless a future cited vision analyzer is implemented.

### Hook Failure

The viewer clicked but left early.

Possible signals:

- weak first 5s, 15s, or 30s retention vs baseline;
- transcript starts with slow context;
- main payoff is delayed;
- timestamped comments mention confusion or slow start.

Constraint:

Precise hook diagnosis requires an audience retention curve or equivalent manual retention evidence. With only average view duration or average view percentage, the system should label the issue as broader watch-time underperformance, not hook failure.

### Retention Or Pacing Failure

The video starts acceptably but loses viewers later.

Possible signals:

- largest retention drop happens after the opening;
- drop interval maps to a repetitive, slow, or unclear transcript section;
- comparable videos maintain stronger retention through similar duration ranges;
- comments mention boredom, repetition, or skipped sections.

Constraint:

Precise pacing diagnosis requires retention drop intervals mapped to transcript or manual script intervals. Transcript-only critique is content evidence, not causal proof.

### Topic-Audience Mismatch

The video may be competent but not aligned with the channel audience's expectations.

Possible signals:

- returning-viewer performance is weak when available;
- subscribed vs unsubscribed or returning vs new viewer evidence when available;
- topic differs from recent winners;
- comments show confusion about why the creator covered this;
- baseline videos in the same style or promise perform differently.

Constraint:

Without audience-segment analytics or strong manual creator context, topic-audience mismatch is capped at low-to-medium confidence.

### Engagement Or Satisfaction Failure

People watched but did not care enough to like, comment, share, subscribe, or continue.

Possible signals:

- retention is acceptable but engagement is below baseline;
- likes, comments, shares, or subscribers gained per view are below baseline;
- subscriber conversion is weak;
- audience sentiment lacks emotional payoff or identity connection.

Constraint:

Raw likes and comments are not enough. Engagement must be normalized by opportunity. If engagement is proportionate to views, it belongs in "what to ignore."

### Distribution Expansion Failure

The video started well but failed to expand.

Possible signals:

- early metrics look healthy;
- traffic or views trend slows abruptly;
- performance is stronger with core audiences than broader audiences when available;
- topic has limited audience ceiling.

Constraint:

Never claim to know YouTube's internal ranking model. Say:

```text
We cannot see YouTube's internal ranking model, but the visible signals suggest the video may have struggled to expand beyond its initial audience.
```

Distribution expansion cannot be a primary diagnosis without traffic-source, time-trend, or audience-segment evidence. Without those signals, label it as a possible distribution limit, not a primary bottleneck.

### Unclear Or Mixed Signal

The evidence does not support one confident bottleneck.

This must be a first-class product state, not a failure. The report should rank hypotheses, list missing evidence, and ask targeted questions.

## 9. Report Structure

The report should be compact-first and evidence-card-first, not essay-first. Serious creators should see the decision and the supporting moments quickly, then expand into details when needed.

Required sections:

1. Executive summary.
2. Evidence quality and confidence.
3. Performance funnel diagnosis.
4. Main bottleneck or insufficient-evidence state.
5. Supporting evidence.
6. Baseline comparison.
7. Likely causes ranked by confidence.
8. What to focus on.
9. What to ignore.
10. Next-video improvement plan.
11. Hook, title, and structure rewrites.
12. Follow-up questions or missing-data requests, if needed.

Default UI shape:

- video title and thumbnail;
- primary answer if the evidence gate passes, or `No confident primary bottleneck yet`;
- confidence label with a plain reason;
- evidence quality strip;
- one short `what this means` paragraph;
- one primary next action;
- compact baseline/metric evidence strip;
- what to focus on;
- what to ignore;
- next-video plan;
- hook/title/structure rewrites;
- expandable baseline, retention, transcript, comment, metric, and limitation details.

Detailed metrics should support the diagnosis rather than dominate the page. Full metric tables, baseline membership, retention point details, comment samples, and citation mapping belong behind `View evidence`.

Charts should be sparse and takeaway-led. Use a retention-vs-baseline line chart when retention data is available and small baseline bars for a few key metrics. Every chart needs a plain-language takeaway beside it.

Follow-up chat should be visually secondary as `Ask about this report`, not a full-screen chatbot. It can answer only from the stored analysis snapshot unless the user explicitly refreshes data, adds context, or invokes a deeper analyzer.

Evidence cards should use the embedded YouTube player and timestamps rather than generated video clips for MVP. A typical card should include:

- timestamp range, such as `00:18-00:32`;
- "jump to moment" player action;
- transcript excerpt when available;
- metric evidence, such as retention vs baseline;
- diagnosis explanation;
- recommended action.

## 10. Evidence And Citations

Every factual claim must trace to stored evidence.

Evidence categories:

- authenticated analytics;
- baseline metrics;
- retention intervals;
- transcript intervals;
- comments and timestamped reactions;
- packaging analysis;
- user-provided context or manual metrics.

Every factual report claim must include a machine-readable citation to a stored evidence object. The LLM receives evidence IDs and must cite them in report JSON. The backend must validate citations before saving or displaying a report.

Example citation object:

```json
{
  "source_type": "retention_point",
  "source_id": "analysis_retention_points.id",
  "label": "Retention: 00:18-00:32",
  "timestamp_start": 18,
  "timestamp_end": 32
}
```

Supported citation types:

- `analytics_metric`;
- `baseline_metric`;
- `baseline_video`;
- `retention_point`;
- `transcript_interval`;
- `comment_signal`;
- `packaging_signal`;
- `manual_metric`;
- `user_context`.

Example citation labels:

- `[Analytics: selected video, first 7 days]`
- `[Baseline: last 10 long-form videos]`
- `[Retention: 00:15-00:30]`
- `[Transcript: 00:15-00:30]`
- `[Comments: timestamp reactions around 01:12]`
- `[Packaging: title promise clarity]`

The exact citation schema can evolve, but the report must not cite fake or model-invented evidence.

## 11. Analyzer Architecture

The system is analytics-first and LLM-second.

Deterministic code owns:

- data fetching and normalization;
- baseline selection;
- metric deltas, medians, percentiles, and trends;
- retention-to-transcript mapping;
- comment timestamp extraction;
- candidate bottleneck scores;
- evidence gates;
- confidence levels;
- deterministic diagnosis JSON.

LLMs own:

- creator-friendly explanation;
- transcript, comment, and packaging interpretation inside evidence bounds;
- hook rewrites;
- title rewrites;
- structure recommendations;
- next-video planning;
- follow-up chat grounded in the analysis snapshot.

The LLM does not choose or override the primary bottleneck. If deterministic diagnosis JSON says `insufficient_evidence=true`, the LLM must produce an insufficient-evidence report.

Specialized analyzers:

- `AnalyticsSignalAnalyzer`
- `ContentStructureAnalyzer`
- `AudienceSignalsAgent`
- `PackagingAnalyzer`
- `DiagnosisOrchestrator`
- `CoachLLM`

Sub-agents must return compact JSON evidence.

## 12. Audience Signals Agent

The Audience Signals Agent fetches and analyzes comments without bloating the main diagnosis context.

Responsibilities:

- fetch capped comment threads;
- store raw comments tied to the analysis run;
- extract timestamp mentions such as `0:42`, `1:15`, or `12:03`;
- map timestamped comments to transcript and retention intervals;
- cluster sentiment and themes;
- identify repeated viewer language;
- return compact JSON to the diagnosis engine.

Themes include:

- confusion;
- praise;
- boredom;
- disagreement;
- emotional payoff;
- missing detail;
- title mismatch;
- slow intro;
- pacing;
- strong quote-worthy reactions.

Comments are supporting evidence. The system must account for sample size and representativeness.

Comments can satisfy the content-or-audience evidence gate only as bounded supporting evidence. Comments alone cannot create high confidence. Disabled, unavailable, sparse, or generic comments are neutral, not negative.

## 13. Baseline Rules

Default baseline:

- last 10-20 comparable uploads before the selected video;
- same post-publish window, defaulting to first 7 completed days;
- long-form compared with long-form;
- median baseline by default;
- at least 5 comparable videos for confident baseline.

Exclude or downweight:

- Shorts;
- livestreams and premieres with live-first behavior;
- trailers, announcements, channel updates, and other non-standard uploads;
- podcasts or unusually long videos when the selected video is not that format;
- videos less than 50% or more than 200% of selected video duration unless explicitly marked comparable;
- viral breakouts above a clear outlier threshold, such as more than 3x the channel median first-7-day views, unless comparing against winners is intentional;
- videos published after the selected video;
- uploads with missing critical analytics.

Store baseline membership in the analysis snapshot.

## 14. Data Sources

### YouTube Data API

Used for:

- channel identity;
- owned upload list;
- video metadata;
- title;
- description;
- thumbnails;
- public statistics;
- comments where available.

### YouTube Analytics API

Used for:

- views;
- watch time;
- average view duration;
- average view percentage;
- likes;
- comments;
- shares;
- subscribers gained or lost;
- retention curve;
- traffic source or trend signals where available.

CTR and impressions are optional/manual context in MVP unless a verified platform path is added. Do not present ad or card impression metrics as normal thumbnail CTR/impressions.

Required YouTube Analytics signals are blocking for diagnosis. If they are unavailable, delayed, or partially missing, Candor retries and may move the run to `waiting_for_data`. It should not generate a weak diagnosis without at least one authenticated analytics signal.

### Transcript Sources

Layered transcript strategy:

1. YouTube transcript/caption fast path where available.
2. Groq Whisper fallback from audio.
3. Optional user-provided transcript or script after automated attempts fail.

Transcript acquisition should use bounded retries:

- YouTube captions: 2 attempts for transient errors and no retry for permanent unavailable/disabled states.
- Whisper fallback: 2 attempts for transient extraction/transcription/provider errors, respecting backpressure and duration limits.
- If all attempts fail, mark transcript evidence unavailable, continue analytics-first diagnosis, and ask whether the user has a script or transcript.

### User-Provided Data

Asked only when needed:

- `expected_performance`: free text plus optional reference video;
- `problem_observed`: `low_views`, `impressions_stopped`, `low_ctr`, `low_retention`, `low_engagement`, `worse_than_expected`, or `not_sure`;
- `manual_metrics`: labeled values such as CTR, impressions, or first-30-second retention;
- `intended_audience`: `existing_audience`, `new_audience`, `mixed`, or `unknown`;
- `notes`: free text about topic, packaging, launch context, or creator intent.

Manual context is optional and structured-first, with free-form notes as a fallback. Manual metrics and context must be stored separately and labeled everywhere as user-provided evidence. They can improve confidence but should not be silently mixed into platform analytics snapshots. If added context changes interpretation, create a linked `manual_context_revision` run.

## 15. MVP Scope

MVP must include:

- Candor multi-page SaaS shell with `/`, `/login`, `/auth`, `/app`, and `/faq`;
- Google/YouTube OAuth login;
- encrypted refresh-token storage;
- disconnect and delete-analysis-data paths;
- owned channel/video selection;
- analysis run creation;
- public metadata and transcript ingestion;
- private analytics snapshot;
- baseline builder;
- deterministic diagnosis JSON;
- structured report generation;
- evidence gates and insufficient-evidence state;
- Audience Signals Agent for comments;
- linked retry for failed analysis runs;
- linked refresh and manual-context revision runs;
- `waiting_for_data` state for delayed required analytics or baseline evidence;
- lightweight durable retry metadata for waiting runs;
- explicit per-run `Notify me` consent;
- transactional email provider interface with Resend and a fake test provider;
- follow-up chat attached to the report;
- lightweight report feedback tied to `analysis_run_id`;
- provider-mocked tests.

MVP should avoid:

- Instagram support;
- multi-platform support;
- competitor discovery;
- clickbait title generation;
- standalone title or thumbnail generators;
- copying large creators' videos, formats, thumbnails, titles, or personal style;
- automated thumbnail vision analysis;
- full thumbnail generation;
- user-facing performance scores, grades, or confidence percentages;
- pricing or billing UI;
- revenue analytics;
- team workspaces;
- generic chatbot-first UI;
- continuous whole-channel syncing;
- claims about YouTube's internal algorithm.

## 15.1 Reliability Rules

Reliable and honest diagnosis is the product.

- Do not name a primary bottleneck unless the evidence gate passes.
- Do not show uncited LLM prose as a final diagnosis.
- Validate strict report JSON, required sections, bottleneck consistency, insufficient-evidence state, and citations before display.
- Retry report generation when validation fails.
- If LLM report generation still fails, show a deterministic fallback report generated from diagnosis JSON.
- Confidence is stored as a numeric `0.0-1.0` score but shown as labels with reasons: `High confidence`, `Medium confidence`, `Low confidence`, or `Insufficient evidence`.
- Do not show confidence percentages.
- Hook/title rewrites are allowed when evidence is insufficient, but they must be labeled as low-confidence options tied to ranked hypotheses.

## 15.4 Transactional Email

Email is operational, not marketing. MVP email is limited to:

- diagnosis ready after a `waiting_for_data` run, only if the user clicked `Notify me`;
- analysis failed after retries are exhausted, only if the user clicked `Notify me`;
- optional deletion confirmation.

Do not send newsletters, weekly reports, growth nudges, reactivation emails, or marketing messages.

Notification consent is per run. Store the requested email address, requested timestamp, and send attempts against the relevant `analysis_run`. Do not create account-wide notification preferences in MVP.

## 15.2 Report Feedback

MVP should collect lightweight feedback after a report is read.

Questions:

- "Was this diagnosis useful?" yes/no.
- "Did this match what you saw in YouTube Studio?" yes/no/partly.
- Optional short note.

Product analytics can also track whether the user copies hook, title, or plan outputs.

Feedback is validation data, not diagnosis evidence. Store it against `analysis_run_id`; do not put it in follow-up chat memory, and do not let feedback automatically rewrite the diagnosis.

## 15.3 Data Retention

Retain immutable analysis snapshots and reports until the user deletes them or deletes their account. Do not continuously sync or warehouse the whole channel.

Deletion paths must support:

- disconnect YouTube;
- delete an individual report;
- delete all analysis data;
- delete account.

Deletion must remove database rows and vectors tied to the relevant user or analysis runs.

## 16. V1 Scope

V1 should deepen reliability and workflow:

- saved report history;
- report refresh;
- manual metric enrichment;
- selected reference videos;
- stronger thumbnail vision analysis;
- recurring post-upload reviews;
- improved retention and traffic-source explanations;
- creator-specific recommendation memory.

## 17. V2 Scope

V2 can add reference and competitor analysis:

- paste public competitor/reference videos;
- compare title, thumbnail, transcript, comments, and public metrics;
- build a reference board;
- identify reusable patterns from stronger videos;
- generate next-video briefs from multiple references.

## 18. Long-Term Vision

The long-term product is the creator's performance learning system.

It should answer:

```text
What is this creator learning over time?
What patterns are working for this channel?
What should they repeat?
What should they stop doing?
What should they test next?
```

## 19. One-Line Definition

```text
Candor is a frank, evidence-backed YouTube diagnosis tool that helps creators understand why one video underperformed and what to try next.
```
