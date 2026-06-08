# Agent Notes

## Operating Workflow

- Before implementing any feature or fix, read `AGENTS.md` first and then read `.codex/Progress.md`.
- After each meaningful implementation chunk, update `.codex/Progress.md` with what changed, what was verified, and what remains.
- Update this file when a planning or implementation decision changes the architecture, provider choices, schema, interfaces, security model, or developer workflow.
- For large work, create or update the relevant milestone in `.codex/PLANS.md` before implementation.
- Keep phase documentation current in `docs/phase/` when phase scope changes materially.

## Product Goal

Build Candor, an OAuth-connected YouTube video performance diagnosis tool for serious creators.

The product analyzes one underperforming YouTube video owned by the authenticated creator, compares it against the creator's own channel baseline, identifies the most likely performance bottleneck, and generates a structured post-mortem report with evidence, confidence, limitations, and a next-video improvement plan.

This is not a generic video chatbot and not the old YouTube/Instagram comparison demo. Chat is secondary and must stay attached to a generated report.

## Current Pivot Direction

- The active branch is for the YouTube diagnosis product pivot.
- Refactor the existing app in place on this branch.
- Reuse proven infrastructure where it still fits: FastAPI, Next.js, Postgres, Qdrant, Groq chat, Groq Whisper, YouTube transcript fast path, `yt-dlp`, extraction cache, structured errors, backpressure, and provider-mocked CI.
- Replace the active product contract: one authenticated YouTube creator, one selected owned YouTube video, automatic analysis report first, follow-up chat second.
- Remove Instagram and two-video A/B comparison from the active MVP surface as the pivot progresses.

## MVP Product Requirements

- Google/YouTube OAuth is required for MVP because deep analysis needs private creator analytics.
- Google OAuth is the primary login system for MVP.
- The OAuth consent screen can start in Testing mode with allowlisted users.
- Users connect YouTube, select an owned channel video, and receive an automatic diagnosis report.
- MVP diagnosis is long-form-only. Detect Shorts and exclude them from diagnosis rather than applying long-form assumptions.
- MVP analysis execution uses explicit `analysis_run` statuses: `queued`, `running`, `waiting_for_data`, `needs_input`, `completed`, and `failed`.
- FastAPI background tasks are acceptable for immediate execution, but delayed required YouTube Analytics or baseline data must use lightweight durable retry metadata on `analysis_run`; do not add a full queue system until the product workflow is validated.
- Retrying a failed analysis must create a new `analysis_run` linked by `parent_analysis_run_id`; do not mutate old snapshots or failure records.
- Refreshing analytics or adding manual context that changes interpretation must also create a linked run with `run_reason` set to `refresh` or `manual_context_revision`.
- The system should analyze first and ask clarifying questions only when data is insufficient for a reliable conclusion.
- The default comparison window is the first 7 completed days after publish. Videos from 72 hours to 7 days old can receive lower-confidence early-read reports; videos under 72 hours should generally not receive a primary bottleneck.
- If evidence is insufficient, the product must say so and ask targeted questions instead of producing a weak diagnosis.
- If required core analytics, baseline, selected-video metadata, or ownership/channel verification data is unavailable or partially missing, retry collection and use `waiting_for_data` instead of producing a weak limited report.
- If a run enters `waiting_for_data`, show a `Notify me` action. Email notification is per-run, explicit opt-in only, and should use the creator's verified Google email when available.
- If required data remains unavailable after retry exhaustion, mark the run `failed` with a precise non-blaming reason; do not convert it into a weak diagnosis.
- Follow-up chat must be grounded in the analysis snapshot unless the user explicitly refreshes data, adds manual context, or invokes a deeper analyzer.

## Frontend

- Always use the `/web-design-guidelines` and `/frontend-design` skill for frontend generation or UI review.
- Build a multi-page SaaS application with separate routes:
  - `/` public landing page;
  - `/login` focused sign-in page;
  - `/auth` focused Google/YouTube trust and permission page;
  - `/app` authenticated workspace for video selection and diagnosis;
  - `/faq` supporting trust and education page.
- Keep the UI focused on one job: answering "Why did my video not perform?"
- Expose the best next action by default. Keep secondary options available but hidden behind buttons, menus, or expansion controls.
- Do not bombard the user with dashboards, feature grids, visible advanced settings, or multiple analysis modes.
- Be transparent about what data Candor reads, how it is used, and what it never does.
- Candor must not market itself as a clickbait title generator, thumbnail generator, generic AI coach, or way to copy large creators' videos or style.
- Product tone should feel like an experienced creator friend with evidence: direct, useful, and careful, not flattering, gimmicky, or performatively "brutally honest".
- The first frontend implementation pass should build a polished static shell wired to current `/api/me` and OAuth start plumbing before pretending channel/video/report APIs exist.

### Visual System

- Brand name: Candor.
- Visual psychology: calm diagnostic workspace, not a roast, AI toy, or YouTube clone.
- Red is reserved for errors only; avoid using YouTube red as a brand color.
- Teal is a scarce truth accent and should not dominate surfaces.
- Evidence blue is `#4B6B8C`.
- Amber is reserved for uncertainty, limitations, and missing data.
- Use Inter for product UI and prose with system sans fallback.
- Use tabular numerals for all metrics, report numbers, progress states, tables, charts, and baseline comparisons.
- Use a mono face only for timestamps, evidence IDs, raw metric labels, and compact diagnostic metadata.
- Avoid serif headlines in the core app.

## Evidence Standard

Reliable diagnosis is the product. The system must prefer an honest incomplete answer over confident slop.

A primary bottleneck can be named only when the evidence gate passes:

- At least one authenticated analytics signal.
- At least 5 comparable prior long-form videos in a same-window channel-baseline comparison.
- At least one content or audience signal.
- One candidate bottleneck materially stronger than alternatives.
- At least one contradiction check showing why another plausible bottleneck is less likely.
- A confidence level tied to data completeness.

If this bar is not met, show ranked hypotheses, missing data, and the exact questions or manual metrics needed to improve confidence.

Never show uncited LLM prose as a final diagnosis. Reports must use strict JSON, valid machine-readable citations to stored evidence, and deterministic fallback output if LLM report validation fails.

## Diagnosis Framework

Every diagnosis should follow:

```text
Signal -> Evidence -> Interpretation -> Confidence -> Action
```

The deterministic analytics engine owns metrics, baselines, trends, retention mapping, candidate bottleneck scores, evidence gates, and confidence. The LLM owns explanation, coaching, rewrites, and creator-friendly report language within the deterministic evidence envelope.

## Core Failure Types

- Packaging failure.
- Hook failure.
- Retention or pacing failure.
- Topic-audience mismatch.
- Engagement or satisfaction failure.
- Distribution expansion failure.
- Unclear or mixed signal.

Do not claim certainty about YouTube's internal recommendation model. Use careful language such as "likely," "suggests," and "based on available signals."

## Analyzer Boundaries

Use specialized analyzers with compact typed outputs:

- `AnalyticsSignalAnalyzer`: private metrics, baselines, trends, retention, traffic sources, engagement, subscribers.
- `ContentStructureAnalyzer`: transcript structure, hook timing, payoff timing, pacing sections, retention-to-transcript mapping.
- `AudienceSignalsAgent`: comments, timestamp reactions, sentiment themes, viewer language, audience confusion or praise signals.
- `PackagingAnalyzer`: title, description, promise clarity, thumbnail display context, optional manual packaging context, and optional manual CTR/impression context.
- `DiagnosisOrchestrator`: merges analyzer outputs, applies evidence gates, scores bottlenecks, emits deterministic diagnosis JSON.
- `CoachLLM`: turns diagnosis JSON into report prose, rewrites, next-video plans, and grounded follow-up answers.

Sub-agents should return compact JSON evidence, not long essays.

## OAuth And Privacy Rules

- Use narrow read-only OAuth scopes for MVP:
  - `openid`
  - `email`
  - `profile`
  - `https://www.googleapis.com/auth/youtube.readonly`
  - `https://www.googleapis.com/auth/yt-analytics.readonly`
- Do not request monetary analytics or write/manage scopes in MVP.
- Store refresh tokens encrypted at rest.
- Never expose tokens to the frontend.
- Never log tokens or raw OAuth credentials.
- Add disconnect and delete-analysis-data paths early.
- Transactional email is allowed only for explicit per-run notifications, failed-after-retry notifications, and deletion confirmations. Do not add newsletters, nudges, weekly reports, or marketing email.
- Use Resend behind an email provider interface for MVP transactional email, with a fake provider for tests and local development.
- Store immutable analysis snapshots, not an unlimited analytics warehouse.

## Data Policy

Persist enough data to make reports reproducible:

- selected video metadata and transcript;
- normalized analytics used in the report;
- baseline video IDs and normalized baseline metrics;
- retention points and mapped transcript intervals;
- comment samples and derived audience signals used as evidence;
- packaging signals;
- deterministic diagnosis JSON;
- final report and citations.

Do not continuously sync the creator's whole channel in MVP.

## Baseline Policy

- MVP diagnosis supports long-form only; Shorts are excluded.
- Use videos published before the selected video.
- Compare the same post-publish window, defaulting to the first 7 completed days.
- Prefer median over average.
- Require at least 5 comparable videos for a confident baseline.
- Exclude obvious outliers such as livestreams, trailers, podcasts, extreme duration mismatches, or viral breakouts when they would distort the baseline.
- Store baseline membership explicitly in the analysis snapshot.

## Transcript And Comments

- Keep the YouTube transcript/caption fast path where it works.
- Use bounded retries for transient transcript failures.
- Use Groq Whisper fallback when captions are unavailable or unreliable, also with bounded retries.
- If automated transcript acquisition fails, continue analytics-first diagnosis, mark transcript evidence unavailable, and ask whether the user has a script or transcript.
- Avoid stronger caption-management scopes unless the product explicitly needs private caption files.
- Map retention points to transcript timestamps before the LLM interprets hook or pacing issues.
- Use the Audience Signals Agent for comment analysis. Comments can be strong evidence when users mention timestamps or quote moments, but they are supporting signals and must be weighed by sample size and representativeness.
- Disabled, unavailable, sparse, or generic comments are neutral, not negative.

## Failure-Type Reliability Rules

- Packaging failure cannot be high-confidence primary without CTR/impression context or equivalent click-opportunity evidence. CTR and impressions are optional/manual MVP evidence, not mandatory platform signals.
- MVP does not include automated thumbnail image analysis. Store and display thumbnails, but do not claim thumbnail readability, visual hierarchy, emotional clarity, or title-thumbnail alignment without a future cited vision analyzer.
- Hook failure and retention/pacing failure require retention curve evidence or equivalent manual retention evidence. Average view duration alone is watch-time underperformance, not proof of hook or pacing failure.
- Topic-audience mismatch is capped at low-to-medium confidence without audience-segment analytics or strong labeled creator context.
- Engagement or satisfaction failure must use opportunity-normalized metrics such as likes/comments/shares/subscribers per view, not raw counts.
- Distribution expansion failure requires time-trend, traffic-source, or audience-segment evidence and must not claim knowledge of YouTube's internal recommendation model.
- Manual metrics and user context must be stored and labeled separately from fetched platform analytics.
- Manual context should be structured-first with optional notes: expected performance, observed problem, manual metrics, intended audience, and free-form notes.
- Confidence is stored numerically but shown primarily as labels with reasons, not percentages.

## Schema Direction

Add Alembic migrations now. The old `create_all` approach is no longer enough for OAuth, private analytics, and analysis snapshots.

The new canonical product object is `analysis_run`, not chat session or ingest session.

Expected new tables:

- `users`
- `youtube_channels`
- `oauth_tokens`
- `analysis_runs`
- `analysis_video_snapshots`
- `analysis_metric_snapshots`
- `analysis_baseline_videos`
- `analysis_retention_points`
- `analysis_comment_signals`
- `analysis_manual_evidence`
- `analysis_reports`
- `analysis_report_feedback`
- `analysis_followup_messages`
- `analysis_usage_ledger`
- `analysis_notification_attempts`

Legacy session tables can remain temporarily during migration but should not drive new product behavior.

## Developer Workflow

- Do not hardcode secrets.
- Prefer server-side authorization checks.
- Add tests for new behavior.
- Provider wrappers must keep tests independent of real Google, YouTube, Groq, Qdrant Cloud, and Neon access.
- Run focused tests after each change.
- Run `make ci` before opening a PR when practical.
- Do not rewrite unrelated files.
- Do not introduce new libraries without explaining why in docs or progress notes.

## Source Citation Format

Report citations should point to typed evidence, not invented model labels.

Examples:

- `[Analytics: selected video, first 7 days]`
- `[Baseline: last 10 long-form videos]`
- `[Retention: 00:15-00:30]`
- `[Transcript: 00:15-00:30]`
- `[Comments: timestamp reactions around 01:12]`
- `[Packaging: title promise clarity]`

The final citation schema can change during implementation, but every factual claim must remain traceable to stored analysis evidence.
