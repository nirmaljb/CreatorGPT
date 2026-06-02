# Installation

This guide explains how to set up the app, configure environment variables, run it locally, and deploy the backend to Render.

## System tools

Install these first:

- Python 3.11 or newer
- Node.js 22 or newer
- npm
- `ffmpeg`

`ffmpeg` is needed for reliable audio extraction before transcription.

## Environment file

Create the local environment file:

```bash
cp .env.example .env
```

Then fill in the required backend values:

| Variable | What It Is For |
| --- | --- |
| `GROQ_API_KEY` | Groq chat and Whisper transcription |
| `DATABASE_URL` | Neon Postgres connection string |
| `QDRANT_URL` | Qdrant Cloud URL |
| `QDRANT_API_KEY` | Qdrant Cloud API key |

Optional values are shown in [.env.example](../.env.example).

## Hosted frontend and backend

Set these together to avoid CORS errors:

| Variable | Where To Set It | Example |
| --- | --- | --- |
| `CORS_ORIGINS` | Backend | `https://your-frontend.onrender.com` |
| `CORS_ORIGIN_REGEX` | Backend | Optional trusted preview-domain regex |
| `NEXT_PUBLIC_API_BASE` | Frontend | `https://your-backend.onrender.com` |

Use exact origins when possible. `CORS_ORIGIN_REGEX` is intended only for trusted preview domains.

## Backend defaults

| Variable | Default | What It Controls |
| --- | --- | --- |
| `GROQ_CHAT_MODEL` | `llama-3.3-70b-versatile` | Chat model used for streamed answers |
| `GROQ_TRANSCRIPTION_MODEL` | `whisper-large-v3` | Hosted Whisper model used for transcription |
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Embedding model used for transcript chunks |
| `EMBEDDING_DIMENSIONS` | `384` | Qdrant vector size for the embedding model |
| `QDRANT_COLLECTION` | `creator_video_chunks` | Qdrant collection name |
| `REQUIRE_QDRANT_ON_STARTUP` | `false` | Whether startup fails when Qdrant validation fails |
| `QDRANT_CHECK_COMPATIBILITY` | `false` | Whether Qdrant client checks server version at startup |
| `FORCE_REFRESH` | `false` | Whether extraction cache reads are bypassed |

## Backpressure limits

| Variable | Default | What It Controls |
| --- | --- | --- |
| `MAX_VIDEO_SECONDS` | `600` | Audio download and Groq Whisper window when captions are unavailable |
| `MAX_CONCURRENT_INGESTIONS` | `2` | Active background ingestion sessions accepted by one backend process |
| `MAX_CHUNKS_PER_VIDEO` | `120` | Maximum transcript chunks embedded and stored for each video |
| `MAX_CHAT_HISTORY_MESSAGES` | `12` | Recent chat messages loaded for prompt context and UI reload |
| `MAX_RETRIEVED_CHUNKS` | `8` | Maximum transcript chunks passed into a chat answer |
| `MAX_SESSIONS_PER_IP_PER_HOUR` | `20` | Ingest sessions accepted per IP per hour |

## Install backend dependencies

```bash
python -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
backend/.venv/bin/python -m pip install -r backend/requirements-dev.txt
```

## Install frontend dependencies

```bash
cd frontend
npm ci
cd ..
```

## Start the backend

```bash
backend/.venv/bin/uvicorn backend.app.main:app --reload --reload-dir backend/app
```

The backend starts at `http://127.0.0.1:8000`.

## Start the frontend

In a second terminal:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

If port `3000` is busy, Next.js may choose another port such as `3001`.

## Run with Docker

```bash
docker build -f backend/Dockerfile -t creator-rag-backend .
docker run --rm -p 10000:10000 --env-file .env creator-rag-backend
```

Then open `http://localhost:10000/health`.

## Render backend deployment

The backend can deploy as a Docker web service on Render.

Use these Render settings:

| Setting | Value |
| --- | --- |
| Runtime | Docker |
| Root directory | Blank or `.` |
| Dockerfile path | `./backend/Dockerfile` |
| Docker context | `.` |
| Docker command | Leave blank |
| Health check path | `/health` |

The Docker image installs `ffmpeg`, writes temporary media to `/tmp/creator-rag`, and starts Uvicorn on `0.0.0.0` using Render's `PORT`.

You can also apply [render.yaml](../render.yaml) as a Render Blueprint. It defines the backend Docker service and marks secret values as manual Render environment variables.

## Local checks

Run the same checks as CI:

```bash
make ci
```

This runs backend lint, backend tests, frontend lint, frontend typecheck, frontend build, markdown lint, and a provider-mocked smoke test.

Useful individual commands:

| Command | Purpose |
| --- | --- |
| `make backend-lint` | Run Ruff checks for Python |
| `make backend-tests` | Run backend tests except smoke |
| `make mocked-smoke` | Run the provider-mocked API smoke test |
| `make frontend-lint` | Run frontend ESLint |
| `make frontend-typecheck` | Run TypeScript checks |
| `make frontend-build` | Build the Next.js app |
| `make markdown-lint` | Check Markdown files |
| `make ci` | Run all required checks |

The required CI path uses mocked tests only. It does not need real Groq, Qdrant Cloud, Neon, YouTube, or Instagram access. Real-provider checks should be manual or nightly.
