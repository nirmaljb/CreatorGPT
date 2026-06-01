# Creator Video RAG Comparator

Full-stack Phase 1 implementation for comparing one YouTube video and one Instagram Reel with metadata, transcripts, vector retrieval, and streaming cited chat.

## Stack

- Backend: FastAPI, LangGraph, Groq, FastEmbed, Qdrant Cloud, Neon Postgres
- Frontend: Next.js
- Media: `youtube-transcript-api`, `yt-dlp`, Groq `whisper-large-v3`

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ..
cp .env.example .env
uvicorn backend.app.main:app --reload --reload-dir backend/app
```

`ffmpeg` must be installed for reliable audio extraction. Temporary audio is written outside the repo by default so reload mode does not restart on media-file changes.

YouTube ingestion tries captions first and only falls back to audio download plus Groq `whisper-large-v3` when captions are unavailable. YouTube captions are not capped by `MAX_VIDEO_SECONDS`, so videos longer than 10 minutes can ingest when captions are available. Instagram uses the audio plus Groq Whisper path.

Extractor results are cached in Postgres by platform, URL, cache version, and `MAX_VIDEO_SECONDS` so repeated demos can reuse real metadata and transcripts. Set `FORCE_REFRESH=true` to bypass cache reads and force fresh extraction.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Assignment Evals

After ingesting a YouTube + Instagram session and waiting for `completed`, run the assignment question evals:

```bash
backend/.venv/bin/python scripts/eval_assignment_questions.py \
  --api-base http://127.0.0.1:8000 \
  --session-id <completed-session-id>
```

The eval asks the five required questions, checks that responses streamed successfully and contain citations, verifies numeric answers against Postgres-backed status metadata, and fails if metadata-only questions return transcript chunks, missing follower counts are invented, or hook questions cite chunks outside the first 5 seconds.

## Required Environment

Set these in `.env` before running the backend:

- `GROQ_API_KEY`
- `DATABASE_URL`
- `QDRANT_URL`
- `QDRANT_API_KEY`
- `FORCE_REFRESH` optional, defaults to `false`
