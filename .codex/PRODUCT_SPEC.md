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
5. User asks questions once ingestion is completed.
6. Assistant streams grounded answers with metadata and transcript citations.

## Must-Have Assignment Capabilities

- Accept two video URLs.
- Support YouTube and Instagram inputs.
- Extract metadata: views, likes, comments, creator, follower count, hashtags, upload date, duration.
- Compute engagement rate: `(likes + comments) / views * 100`.
- Extract transcript dynamically through YouTube captions or Groq `whisper-large-v3` fallback.
- Record transcript source as `captions`, `whisper`, or `unavailable`.
- Store raw extractor metadata and per-video extraction failures.
- Support optional `yt-dlp` cookies for YouTube access challenges without fabricating fallback metadata or transcripts.
- Cache real extraction results for repeatable demos, with `FORCE_REFRESH=true` for fresh extraction.
- Chunk and embed transcripts into Qdrant with `session_id` and `video_id` payloads.
- Maintain persisted session and chat history in Postgres.
- Route numeric and creator metadata questions to Postgres metadata tools instead of vector retrieval.
- Route semantic transcript questions to Qdrant retrieval.
- Route mixed comparison questions to both metadata tools and Qdrant retrieval.
- Stream responses.
- Cite sources by video and metadata/chunk.

## Success Criteria

- A clean demo can complete: ingest -> completed status -> chat -> cited answer.
- Metadata questions are answered from Postgres.
- Semantic transcript questions are answered from Qdrant chunks.
- Numeric questions do not depend on vector retrieval.
- Long YouTube videos avoid slow Whisper when captions are available.
- YouTube videos longer than 10 minutes can ingest through captions; the 10-minute cap applies to Whisper/audio fallback.
- Missing social metadata is handled honestly without invented values.
