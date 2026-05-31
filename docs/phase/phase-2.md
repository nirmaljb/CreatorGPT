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
