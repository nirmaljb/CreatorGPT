# Product Spec

## What We Are Building

A full-stack RAG chatbot that compares two creator videos from YouTube or Instagram. Users provide two video URLs, the system extracts metadata and transcript content, computes engagement metrics, stores transcript chunks in a vector database, and answers creator questions with streamed, cited responses.

## For Whom

- Primary user: a creator or creator-ops analyst comparing why one video performed better than another.
- Demo evaluator: a technical reviewer checking whether the system is dynamic, full-stack, grounded, scalable, and engineered beyond prompt-only work.

## Why

Creators need quick, evidence-backed explanations for performance differences. The product combines objective metadata, transcript evidence, and LLM reasoning so the answer can cite what actually happened in each video instead of guessing.

## Core User Journey

1. User opens the Next.js UI.
2. User enters two video URLs and selects each platform.
3. Backend returns a `session_id` immediately.
4. UI shows metadata and progress while ingestion runs.
5. User asks questions once ingestion is ready.
6. Assistant streams grounded answers with metadata and transcript citations.

## Must-Have Assignment Capabilities

- Accept two video URLs.
- Support YouTube and Instagram inputs.
- Extract metadata: views, likes, comments, creator, follower count, hashtags, upload date, duration.
- Compute engagement rate: `(likes + comments) / views * 100`.
- Extract transcript dynamically through YouTube captions or Whisper fallback.
- Chunk and embed transcripts into Qdrant with `session_id` and `video_id` payloads.
- Maintain persisted session and chat history in Postgres.
- Stream responses.
- Cite sources by video and metadata/chunk.

## Success Criteria

- A clean demo can complete: ingest -> ready status -> chat -> cited answer.
- Metadata questions are answered from Postgres.
- Semantic transcript questions are answered from Qdrant chunks.
- Long YouTube videos avoid slow Whisper when captions are available.
- Missing social metadata is handled honestly without invented values.
