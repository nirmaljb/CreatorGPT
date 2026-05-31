# Creator Video RAG Comparator

Full-stack Phase 1 implementation for comparing one YouTube video and one Instagram Reel with metadata, transcripts, vector retrieval, and streaming cited chat.

## Stack

- Backend: FastAPI, LangGraph, Groq, FastEmbed, Qdrant Cloud, Neon Postgres
- Frontend: Next.js
- Media: `youtube-transcript-api`, `yt-dlp`, `faster-whisper`

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

YouTube ingestion tries captions first and only falls back to audio download plus Whisper when captions are unavailable. Instagram uses the audio plus Whisper path.

## Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:3000`.

## Required Environment

Set these in `.env` before running the backend:

- `GROQ_API_KEY`
- `DATABASE_URL`
- `QDRANT_URL`
- `QDRANT_API_KEY`
