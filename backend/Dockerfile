FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive \
    TMP_DIR=/tmp/creator-rag \
    PORT=10000

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends ca-certificates ffmpeg \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /tmp/creator-rag

COPY backend/requirements.txt /app/backend/requirements.txt
RUN python -m pip install --upgrade pip \
    && python -m pip install -r /app/backend/requirements.txt

COPY backend /app/backend

EXPOSE 10000

CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-10000}"]
