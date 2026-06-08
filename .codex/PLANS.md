# Plans

## Milestone 0: Pivot Documentation And Product Contract

### Scope

- Replace old comparison-demo docs with the YouTube diagnosis product direction.
- Define the report-first MVP.
- Define OAuth, privacy, schema, and analyzer boundaries.
- Define the first implementation milestone.

### Acceptance Criteria

- `AGENTS.md` reflects the new product and workflow.
- `.codex/PRODUCT_SPEC.md` describes the YouTube diagnosis product.
- `.codex/ARCHITECTURE.md` describes `analysis_run`, OAuth, snapshots, analyzers, and report-first flow.
- `README.md` introduces the pivot product clearly.
- `.codex/Progress.md` records the pivot status and next step.

## Milestone 1: OAuth-Connected Analysis Skeleton

### Scope

- Build the Candor multi-page SaaS shell before deeper backend slices:
  - public landing page at `/` with one report preview and one `Connect YouTube` CTA;
  - focused sign-in page at `/login`;
  - focused Google/YouTube trust and permission detail page at `/auth`;
  - authenticated workspace shell at `/app`;
  - expanded trust FAQ at `/faq`;
  - Candor visual system with evidence blue `#4B6B8C`, scarce teal truth accents, amber uncertainty states, red errors only, Inter, tabular numerals, and mono timestamps/evidence IDs.
- Add Alembic migration workflow.
- Add schema for users, channels, OAuth tokens, and analysis runs.
- Implement Google OAuth start/callback.
- Store encrypted refresh tokens.
- Add `GET /me`.
- Add `POST /youtube/disconnect`.
- Add provider wrappers for YouTube channel identity and owned upload listing.
- Support multiple authenticated YouTube channels with one active channel in the MVP UI.
- Reject Shorts from MVP diagnosis.
- Add explicit `analysis_run` statuses for analysis execution: `queued`, `running`, `waiting_for_data`, `needs_input`, `completed`, and `failed`.
- Add lightweight durable retry metadata for delayed required data: `next_retry_at`, `retry_count`, and `last_data_wait_reason`.
- Add linked retry semantics for failed analysis runs.
- Add `run_reason` and linked-run semantics for refresh and manual-context revisions.
- Add a minimal frontend product path: connect YouTube, select one owned long-form video, and create an analysis run.

### Acceptance Criteria

- A test user can connect YouTube in OAuth Testing mode.
- The backend stores the user, channel, and encrypted refresh token.
- The frontend can show the connected channel.
- Users with multiple channels can choose one active channel.
- The frontend can list owned uploads.
- Shorts are detected and excluded from diagnosis creation.
- Creating an analysis run persists a row with `queued` or `running` status and returns an `analysis_run_id`.
- Required analytics, baseline, selected-video metadata, or ownership/channel delays can move a run to `waiting_for_data` instead of producing a weak limited report.
- Retrying a failed analysis run creates a new row with `parent_analysis_run_id`.
- Refreshing or revising with manual context creates a new linked row with the appropriate `run_reason`.
- Tests mock Google and YouTube providers.
- The frontend route split keeps landing, authentication, and the working application separate.
- The frontend avoids dashboard overload, visible scores, clickbait-generator framing, thumbnail-generator framing, and copy-big-creators framing.

## Milestone 2: Analysis Snapshot Foundation

### Scope

- Fetch selected video metadata.
- Fetch transcript through existing YouTube transcript path or Groq Whisper fallback.
- Retry transcript acquisition with bounded retry policy and support optional manual transcript/script evidence.
- Fetch private analytics needed for first diagnosis.
- Select baseline videos from the authenticated channel.
- Store immutable analysis snapshots.
- Store optional manual metrics and user context separately from platform analytics.
- Move vector payloads from `session_id` to `analysis_run_id`.

### Acceptance Criteria

- The system can create a completed analysis snapshot without generating a final diagnosis.
- Baseline membership is stored and inspectable.
- Baseline uses the first 7 completed days by default and marks early-read runs.
- Transcript chunks are tied to `analysis_run_id`.
- Missing transcripts degrade content confidence without blocking analytics snapshots.
- Missing required analytics or baseline data blocks final diagnosis, enters `waiting_for_data`, and resumes only after retry succeeds.
- Provider-mocked tests cover video metadata, analytics snapshots, transcript fallback, and baseline selection.

## Milestone 2A: Waiting Data And Transactional Notification

### Scope

- Implement `waiting_for_data` as a first-class run state.
- Add retry scheduling metadata to waiting analysis runs.
- Add a lightweight scheduled backend check for waiting runs.
- Add `Check again now`.
- Add explicit per-run `Notify me` consent.
- Add an `EmailProvider` interface.
- Add `ResendEmailProvider` and `FakeEmailProvider`.
- Store notification attempts against `analysis_run_id`.
- Send diagnosis-ready and retry-exhausted failure emails only when the user requested notification for that run.

### Acceptance Criteria

- Required analytics, baseline, selected-video metadata, and ownership/channel verification delays use `waiting_for_data`.
- Transcript, comments, optional manual context, optional CTR, and optional impressions do not block a report after bounded retries.
- Waiting runs survive API restarts through durable retry metadata.
- Retry exhaustion becomes terminal `failed` with a precise non-blaming reason.
- No email is sent unless the user clicks `Notify me` for that run.
- Tests use the fake provider and do not call Resend.

## Milestone 3: Deterministic Diagnosis Engine

### Scope

- Implement retention-to-transcript mapping.
- Implement candidate bottleneck scoring.
- Implement contradiction checks.
- Implement evidence gate.
- Store both numeric confidence score and user-facing confidence label.
- Emit deterministic diagnosis JSON.
- Add insufficient-evidence output shape.

### Acceptance Criteria

- The engine refuses to name a primary bottleneck when evidence is insufficient.
- Fewer than 5 comparable prior long-form baseline videos prevents confident primary-bottleneck diagnosis.
- Hook and pacing diagnoses require retention curve or equivalent manual retention evidence.
- Packaging cannot be high-confidence primary without CTR/impression or equivalent click-opportunity evidence.
- Packaging analysis does not include automated thumbnail vision in MVP.
- Engagement diagnosis uses opportunity-normalized metrics.
- Hook, pacing, packaging, engagement, topic-audience, and distribution hypotheses have explicit evidence and limitations.
- Unit tests cover evidence thresholds, confidence, and no-slop behavior.

## Milestone 4: Audience Signals Agent

### Scope

- Fetch capped YouTube comment threads.
- Store raw comment samples tied to analysis runs.
- Extract timestamp mentions.
- Map timestamp reactions to transcript and retention intervals.
- Cluster comment themes and viewer language into compact JSON.

### Acceptance Criteria

- Raw comment text does not bloat the main diagnosis prompt.
- The agent returns compact structured evidence.
- Comments are treated as supporting evidence with sample-size limitations.
- Tests cover timestamp extraction and output shape.

## Milestone 5: Report-First UI And Coach LLM

### Scope

- Generate report prose from deterministic diagnosis JSON.
- Build report page sections:
  - summary;
  - evidence quality;
  - funnel diagnosis;
  - main bottleneck or insufficient evidence;
  - baseline comparison;
  - likely causes;
  - what to focus on;
  - what to ignore;
  - next-video plan;
  - hook/title/structure rewrites.
- Render timestamped evidence cards with embedded YouTube player seek actions.
- Render compact evidence strips by default and full evidence behind `View evidence`.
- Use confidence labels with reasons, not percentages.
- Do not render user-facing scores, grades, virality scores, hook scores, or thumbnail scores.
- Keep follow-up chat as a secondary `Ask about this report` panel.
- Validate strict report JSON and machine-readable citations before display.
- Add deterministic fallback report when LLM report validation fails.
- Add lightweight report feedback capture tied to `analysis_run_id`.
- Add grounded follow-up chat attached to the report.

### Acceptance Criteria

- The app opens into an actual analysis workflow, not an empty chatbot.
- The report never invents analytics.
- Every factual claim cites stored evidence.
- Invalid report JSON or citations are rejected before display.
- Report feedback records usefulness, perceived accuracy against YouTube Studio, optional notes, and copied-output events without mutating the diagnosis.
- Follow-up answers cite stored analysis evidence.
- Missing data prompts are targeted and actionable.
- Insufficient evidence is a first-class report state with ranked hypotheses, missing evidence, and 1-3 targeted asks.
- Title and packaging rewrites are presented as diagnosis follow-through, not a standalone generator.

## Milestone 6: Reliability, Privacy, And Demo Readiness

### Scope

- Add disconnect and delete-analysis-data verification.
- Add provider-mocked CI coverage for the full analysis skeleton.
- Add provider-mocked CI coverage for transactional email.
- Add docs for OAuth setup and local development.
- Remove or isolate old YouTube/Instagram comparison routes and UI.
- Rehearse private-test demo.

### Acceptance Criteria

- `make ci` passes without real Google, YouTube, Groq, Qdrant, Neon, or Resend credentials.
- OAuth secrets are never logged.
- Data deletion removes snapshots, comments, reports, vectors, and follow-ups.
- Demo flow is stable for an allowlisted creator account.
