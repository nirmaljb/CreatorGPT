# FAQ

This FAQ answers the questions most likely to come up in a demo or review. The answers use simple language, but they still reflect the current architecture and tradeoffs.

## Questions

1. [Can you walk me through the full system architecture from URL input to streamed cited answer?](#1-can-you-walk-me-through-the-full-system-architecture-from-url-input-to-streamed-cited-answer)
2. [Why did you choose FastAPI, Next.js, LangGraph, Postgres, Qdrant, Groq, and FastEmbed?](#2-why-did-you-choose-fastapi-nextjs-langgraph-postgres-qdrant-groq-and-fastembed)
3. [Why do you use both Postgres and Qdrant instead of storing everything in one database?](#3-why-do-you-use-both-postgres-and-qdrant-instead-of-storing-everything-in-one-database)
4. [What exactly is the source of truth for video metadata, transcript chunks, chat history, and citations?](#4-what-exactly-is-the-source-of-truth-for-video-metadata-transcript-chunks-chat-history-and-citations)
5. [How does the ingestion pipeline work step by step?](#5-how-does-the-ingestion-pipeline-work-step-by-step)
6. [Why does ingestion run asynchronously, and what would break if it ran inside the request?](#6-why-does-ingestion-run-asynchronously-and-what-would-break-if-it-ran-inside-the-request)
7. [How would queues scale the ingestion pipeline in production?](#7-how-would-queues-scale-the-ingestion-pipeline-in-production)
8. [Why should ingestion be queued but chat stay synchronous with SSE streaming?](#8-why-should-ingestion-be-queued-but-chat-stay-synchronous-with-sse-streaming)
9. [How does YouTube ingestion work, and why do you try captions before Whisper?](#9-how-does-youtube-ingestion-work-and-why-do-you-try-captions-before-whisper)
10. [How does Instagram ingestion work, and how do you handle missing or unavailable metadata?](#10-how-does-instagram-ingestion-work-and-how-do-you-handle-missing-or-unavailable-metadata)
11. [How do you compute engagement rate, and what happens when views, likes, or comments are unavailable?](#11-how-do-you-compute-engagement-rate-and-what-happens-when-views-likes-or-comments-are-unavailable)
12. [What is your chunking strategy, and why are first-5-second hook chunks treated specially?](#12-what-is-your-chunking-strategy-and-why-are-first-5-second-hook-chunks-treated-specially)
13. [Why did you use FastEmbed with `BAAI/bge-small-en-v1.5`, and what would changing embedding models require?](#13-why-did-you-use-fastembed-with-baaibge-small-en-v15-and-what-would-changing-embedding-models-require)
14. [How does Qdrant retrieval work, and why do comparison questions retrieve separately from Video A and Video B?](#14-how-does-qdrant-retrieval-work-and-why-do-comparison-questions-retrieve-separately-from-video-a-and-video-b)
15. [Why did you build deterministic LangGraph routing instead of using an LLM router?](#15-why-did-you-build-deterministic-langgraph-routing-instead-of-using-an-llm-router)
16. [Why do numeric and creator questions bypass Qdrant and use typed Postgres metadata tools?](#16-why-do-numeric-and-creator-questions-bypass-qdrant-and-use-typed-postgres-metadata-tools)
17. [How do you prevent hallucinated metrics or fabricated citations?](#17-how-do-you-prevent-hallucinated-metrics-or-fabricated-citations)
18. [How does memory work across chat turns, and how do you prevent unbounded context growth?](#18-how-does-memory-work-across-chat-turns-and-how-do-you-prevent-unbounded-context-growth)
19. [What are the main cost drivers at 1000 creators per day, and how does your system reduce cost?](#19-what-are-the-main-cost-drivers-at-1000-creators-per-day-and-how-does-your-system-reduce-cost)
20. [What would you change first to make this production-ready for 10,000 users?](#20-what-would-you-change-first-to-make-this-production-ready-for-10000-users)

## 1. Can you walk me through the full system architecture from URL input to streamed cited answer?

The user enters two video URLs in the Next.js frontend. The frontend sends them to `POST /ingest`.

The FastAPI backend validates the URLs, checks simple backpressure limits, creates a session in Postgres, and returns a `session_id` right away. The heavier ingestion work continues in the background.

During ingestion, the backend extracts metadata, gets transcripts, chunks the transcript text, creates embeddings with FastEmbed, and stores those vectors in Qdrant. Durable state, such as session status, metadata, chat history, extraction cache, and usage data, stays in Postgres.

When the user asks a question, `POST /chat` routes the question through LangGraph. Numeric questions use Postgres metadata tools. Transcript questions use Qdrant. Mixed comparison questions use both. The backend streams the final Groq answer back to the frontend with SSE events and exact citations like `[Video A metadata]` or `[Video B, chunk 2, 00:11-00:24]`.

## 2. Why did you choose FastAPI, Next.js, LangGraph, Postgres, Qdrant, Groq, and FastEmbed?

FastAPI is a good fit because the extraction, transcription, embedding, and RAG code is Python-heavy. It works well with `yt-dlp`, Groq transcription, LangGraph, Qdrant, and background ingestion.

Next.js is used for the frontend because it is part of the assignment stack and is fast to ship with React and TypeScript.

LangGraph gives the chat path an explicit flow. The app can route questions to metadata tools, transcript retrieval, hook retrieval, or mixed comparison logic instead of treating every question the same way.

Postgres stores durable app state. Qdrant stores searchable transcript vectors. Groq provides fast hosted chat and Whisper transcription. FastEmbed with `BAAI/bge-small-en-v1.5` gives local, low-cost embeddings that match the short transcript chunk use case.

## 3. Why do you use both Postgres and Qdrant instead of storing everything in one database?

Postgres and Qdrant solve different problems.

Postgres is the source of truth for structured data: sessions, video metadata, raw extractor metadata, chat messages, extraction cache, and usage ledger rows. It is good at exact lookups, durable records, constraints, and reporting.

Qdrant is built for vector search. It finds transcript chunks that are semantically similar to a user question. That is a different access pattern than asking Postgres for a known session row or exact metric.

Using both keeps numeric facts reliable and transcript search fast.

## 4. What exactly is the source of truth for video metadata, transcript chunks, chat history, and citations?

Postgres is the source of truth for video metadata, raw extractor metadata, session status, chat history, extraction cache, and usage ledger rows.

Qdrant stores embedded transcript chunks for retrieval. Each chunk includes payload fields such as `session_id`, `video_id`, `chunk_index`, timestamps, `is_hook`, and the citation source tag.

Citations come from stored data, not from the model inventing labels. Metadata citations use `[Video A metadata]` or `[Video B metadata]`. Transcript citations use the chunk payload, such as `[Video A, chunk 3, 00:12-00:27]`.

## 5. How does the ingestion pipeline work step by step?

The backend first validates the requested platform and URL for each slot.

Then it checks process-local limits such as concurrent ingestions and per-IP hourly sessions. If the request is allowed, it creates a Postgres session and returns the `session_id`.

In the background, ingestion loads metadata from cache or extracts fresh metadata. It stores metadata for both videos first so the status endpoint becomes useful early.

After metadata is stored, each video runs transcript and vector work. YouTube tries captions first. If captions are not available, it uses audio download and Groq Whisper. Instagram uses audio download and Groq Whisper.

The transcript is normalized into timed words, chunked, embedded, and written to Qdrant. The session finishes as `completed` when both videos are processed, or `failed` if a required provider step fails.

## 6. Why does ingestion run asynchronously, and what would break if it ran inside the request?

Ingestion can take a while. Metadata scraping, audio download, transcription, chunking, embedding, and vector upsert are all slower than a normal web request.

If all of that ran inside `POST /ingest`, the browser would wait for a long time, hosted platforms could time out the request, and users would not see progress. A slow or failed provider call could also tie up API workers.

Returning a `session_id` immediately makes the app responsive. The frontend can poll `GET /status/{session_id}` and show progress while the backend keeps working.

## 7. How would queues scale the ingestion pipeline in production?

The current app uses FastAPI background tasks because that is enough for a demo. In production, ingestion should move to a durable queue.

A queue would let the API accept work quickly, store a job, and let separate worker processes run extraction and transcription. Workers could scale independently from the API. Failed jobs could retry with backoff. Long jobs would survive API restarts. A queue would also make it easier to enforce global concurrency limits across many backend instances.

Good production choices would include a managed queue, a worker system, shared rate limiting, and clear job states stored in Postgres.

## 8. Why should ingestion be queued but chat stay synchronous with SSE streaming?

Ingestion is long-running batch work. It has many external steps and does not need to hold an open browser response. That makes it a natural fit for a queue.

Chat is interactive. The user expects to see the answer as it is generated. SSE streaming keeps the request open and sends tokens, sources, route data, and completion events in real time.

So the best split is: queue ingestion because it is slow background work, and keep chat synchronous because it is a live user interaction.

## 9. How does YouTube ingestion work, and why do you try captions before Whisper?

YouTube ingestion first extracts metadata. It then tries `youtube-transcript-api` for captions.

Captions are the cheapest and fastest path. They avoid audio download, avoid Whisper cost, and can work for long YouTube videos without being capped by `MAX_VIDEO_SECONDS`.

If captions are missing or fail, the backend falls back to `yt-dlp` audio extraction and Groq `whisper-large-v3`. The audio fallback is limited by `MAX_VIDEO_SECONDS` so one long video does not consume too much transcription time.

Some YouTube videos may require `YTDLP_COOKIES_PATH` when YouTube returns sign-in or bot-check challenges. The app reports that as a visible error instead of creating fake data.

## 10. How does Instagram ingestion work, and how do you handle missing or unavailable metadata?

Instagram ingestion uses the Instagram extractor path. It gets metadata through `yt-dlp` when available, downloads temporary audio, and uses Groq Whisper for transcription.

Instagram does not always expose every metric. Views, followers, or other fields may be unavailable depending on the Reel, account, cookies, or platform behavior.

The app keeps unknown strings as `unknown`. Some stored integer columns may default to `0` for compatibility, but availability flags decide what the UI and chat show. If a metric was not actually available from the extractor, the answer should say `unavailable`, not pretend the value is zero.

## 11. How do you compute engagement rate, and what happens when views, likes, or comments are unavailable?

The engagement rate is based on available engagement counts divided by views. In simple terms, it is:

```text
(likes + comments) / views
```

The app only treats that as complete when the needed values are available. Views are especially important because they are the denominator.

If views are unavailable for a video, the system marks the engagement comparison as incomplete. It should not declare a winner from a missing denominator. If likes or comments are unavailable, the answer should explain that the metric is incomplete instead of inventing a number.

## 12. What is your chunking strategy, and why are first-5-second hook chunks treated specially?

Transcripts are normalized into timed words and then grouped into chunks with timestamps. Each chunk gets a source tag and is embedded into Qdrant.

The first few seconds of a short-form video are especially important because that is where the hook usually happens. The app marks early chunks with `is_hook=true`, and hook comparison questions retrieve those chunks with a Qdrant payload filter.

That prevents a "compare the first 5 seconds" question from retrieving a random later moment just because it is semantically similar.

## 13. Why did you use FastEmbed with `BAAI/bge-small-en-v1.5`, and what would changing embedding models require?

`BAAI/bge-small-en-v1.5` is small, local, fast, and good enough for short transcript chunks. It avoids paying a hosted embedding provider for every chunk during testing.

The model produces 384-dimensional vectors. The Qdrant collection is configured for that dimension.

Changing embedding models would require updating the embedding provider wrapper, changing `EMBEDDING_DIMENSIONS`, recreating or migrating the Qdrant collection, and re-embedding stored transcript chunks. For example, OpenAI `text-embedding-3-small` uses 1536 dimensions, so it cannot be mixed into the existing 384-dimensional collection.

## 14. How does Qdrant retrieval work, and why do comparison questions retrieve separately from Video A and Video B?

Each transcript chunk is embedded and stored in Qdrant with payload fields for session, video, timestamps, and hook status.

For a single-video question, the system filters retrieval to that video. For hook questions, it filters to `is_hook=true`. For comparison questions, it retrieves from Video A and Video B separately, then merges the evidence.

This matters because one global search can return mostly one video. Balanced retrieval makes sure both videos are represented in comparison answers.

## 15. Why did you build deterministic LangGraph routing instead of using an LLM router?

The router is rules-first because the assignment questions need predictable behavior. A deterministic router is cheaper, easier to test, easier to debug, and easier to explain.

The current routes are `METADATA_ONLY`, `TRANSCRIPT_ONLY`, `HOOK_COMPARISON`, `MIXED_COMPARISON`, `IMPROVEMENT_SUGGESTION`, and `FOLLOW_UP`.

An LLM classifier could be added later if evals show that rules miss important phrasing. For now, deterministic routing gives better demo safety.

## 16. Why do numeric and creator questions bypass Qdrant and use typed Postgres metadata tools?

Qdrant is good for finding relevant transcript text. It is not the right source for exact numbers like views, likes, comments, follower count, duration, or engagement rate.

Numeric and creator questions use typed Postgres tools such as `get_video_metrics`, `get_creator_info`, and `get_engagement_comparison`. These tools read structured metadata from Postgres and return known fields.

That reduces hallucination risk and avoids asking a language model to infer numbers from transcript text.

## 17. How do you prevent hallucinated metrics or fabricated citations?

The app separates exact facts from semantic transcript evidence.

Numeric facts come from Postgres metadata tools. Transcript claims come from Qdrant chunks. The prompt tells the model to cite exact source tags only. The eval suite checks citation shape, metadata citations, transcript citations, unavailable metrics, and route behavior.

The app also does not silently fall back to fake metadata or fake transcripts. If extraction, transcription, retrieval, or provider calls fail, the user should see a structured error instead of a fabricated answer.

## 18. How does memory work across chat turns, and how do you prevent unbounded context growth?

Chat messages are stored in Postgres. When the user asks a new question, the backend loads recent chat history and uses it as context.

The number of messages loaded is capped by `MAX_CHAT_HISTORY_MESSAGES`. That keeps prompts from growing without limit and helps control latency and token cost.

Follow-up handling is intentionally simple. The system resolves obvious references like "that video", "their", or "what about B" from recent chat history, then routes the resolved question again.

## 19. What are the main cost drivers at 1000 creators per day, and how does your system reduce cost?

The main cost drivers are transcription seconds, chat tokens, embedding work, Qdrant storage/search, Postgres storage, and repeated extraction work.

The app reduces cost in several ways. YouTube captions are used before Whisper, so many YouTube videos avoid transcription cost. Extraction results are cached in Postgres for repeated demos. Transcript chunks are capped before embedding. Retrieved chunks and chat history are capped before prompting. Numeric questions bypass Qdrant retrieval and use Postgres metadata tools.

The usage ledger records signals like transcribed seconds, chunk count, embedding count, chat tokens, model names, cache hits, and cache misses. That gives a starting point for cost analysis before scaling.

## 20. What would you change first to make this production-ready for 10,000 users?

The first change would be moving ingestion to a durable queue with separate workers. That would make long jobs reliable, retryable, and scalable outside the API process.

The next changes would be shared rate limiting, user accounts and authorization, Alembic migrations, provider health monitoring, alerting, better retry controls, and stronger operational dashboards.

After that, I would add nightly real-provider evals, richer citation inspection in the UI, and retrieval improvements such as reranking or hybrid search only if eval results show a real quality gap.
