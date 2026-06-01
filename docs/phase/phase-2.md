# Phase 2 — Grounded Intelligence

## Scope

Phase 2 improves answer grounding and routing so the chatbot uses the right source for the right type of question.

Included in this phase:

- Add LangGraph routing for numeric, semantic, hook, and recommendation questions.
- Use typed metadata tools for numeric questions instead of free-form SQL or vector retrieval.
- Use transcript retrieval only for semantic and recommendation questions.
- Use first-5-second chunks for hook comparison.
- Add citation validation for metadata and transcript claims.
- Add an eval script for the assignment's required question set.

Out of scope for this phase:

- Major UI redesign.
- Multi-user auth.
- Production monitoring.
- Full hybrid search or reranking unless eval results prove it is necessary.

## Current Eval Harness

`backend.evals.assignment_eval` runs the assignment's five required questions against a completed backend session:

- What is the engagement rate of each video?
- Who is the creator of Video B and what is their follower count?
- Compare the hooks in the first 5 seconds.
- Why did Video A get more engagement than Video B?
- Suggest improvements for B based on what worked in A.

The eval uses the existing streaming `/chat` API. It validates that responses stream to a successful done event, answers are non-empty and cited, numeric answers match available Postgres-backed status metadata, unavailable metrics are stated as unavailable, metadata-only questions return metadata sources without transcript chunks, hook questions use first-5-second chunk sources, and mixed comparison questions include transcript evidence from both videos.

Run it with:

```bash
backend/.venv/bin/python scripts/eval_assignment_questions.py \
  --api-base http://127.0.0.1:8000 \
  --session-id <completed-session-id>
```
