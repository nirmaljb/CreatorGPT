## Parent PRD

`issues/prd.md`

## What to build

Acquire the selected video's transcript, store source-labeled transcript chunks, and map retention drop candidates to transcript intervals and embedded YouTube player seek targets for admin review.

## Acceptance criteria

- [ ] Transcript acquisition tries the existing YouTube transcript/caption fast path first, then bounded retries, then Groq Whisper fallback within a configurable transcription cap, then manual transcript/script fallback when automated acquisition fails.
- [ ] Transcript chunks are stored for the selected video with source labels, timestamps, coverage quality, and run linkage; baseline transcripts are not pulled automatically.
- [ ] Retention-to-transcript mapping only claims coverage for intervals where transcript data exists and marks unavailable or partial intervals clearly.
- [ ] The admin dashboard shows transcript coverage quality, mapped retention intervals, transcript excerpts around drop candidates, and an embedded YouTube player with timestamp jump actions.
- [ ] If automated transcript acquisition fails, the run can still proceed with analytics-first evidence and a targeted needs-input prompt for manual transcript/script.
- [ ] Usage ledger entries record transcript source, transcribed seconds, retry/error counts, and transcript chunk counts.
- [ ] Tests cover transcript fast path, retry behavior, Whisper fallback, manual transcript fallback, transcription cap handling, source labeling, interval-level coverage, retention-to-transcript mapping, embedded player timestamp links, and analytics-first fallback.

## Blocked by

- Blocked by `issues/008-capture-retention-evidence-and-drop-candidates.md`

## User stories addressed

- User story 65
- User story 67
- User story 68
