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

- Add Alembic migration workflow.
- Add schema for users, channels, OAuth tokens, and analysis runs.
- Implement Google OAuth start/callback.
- Store encrypted refresh tokens.
- Add `GET /me`.
- Add `POST /youtube/disconnect`.
- Add provider wrappers for YouTube channel identity and owned upload listing.
- Support multiple authenticated YouTube channels with one active channel in the MVP UI.
- Reject Shorts from MVP diagnosis.
- Add explicit `analysis_run` statuses for FastAPI background-task execution.
- Add linked retry semantics for failed analysis runs.
- Add `run_reason` and linked-run semantics for refresh and manual-context revisions.
- Add a minimal frontend path:
  - Connect YouTube;
  - select owned video;
  - create analysis run.

### Acceptance Criteria

- A test user can connect YouTube in OAuth Testing mode.
- The backend stores the user, channel, and encrypted refresh token.
- The frontend can show the connected channel.
- Users with multiple channels can choose one active channel.
- The frontend can list owned uploads.
- Shorts are detected and excluded from diagnosis creation.
- Creating an analysis run persists a row with `queued` or `running` status and returns an `analysis_run_id`.
- Retrying a failed analysis run creates a new row with `parent_analysis_run_id`.
- Refreshing or revising with manual context creates a new linked row with the appropriate `run_reason`.
- Tests mock Google and YouTube providers.

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
- Provider-mocked tests cover video metadata, analytics snapshots, transcript fallback, and baseline selection.

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

## Milestone 6: Reliability, Privacy, And Demo Readiness

### Scope

- Add disconnect and delete-analysis-data verification.
- Add provider-mocked CI coverage for the full analysis skeleton.
- Add docs for OAuth setup and local development.
- Remove or isolate old YouTube/Instagram comparison routes and UI.
- Rehearse private-test demo.

### Acceptance Criteria

- `make ci` passes without real Google, YouTube, Groq, Qdrant, or Neon credentials.
- OAuth secrets are never logged.
- Data deletion removes snapshots, comments, reports, vectors, and follow-ups.
- Demo flow is stable for an allowlisted creator account.
