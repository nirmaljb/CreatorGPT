import logging
import re
from urllib.parse import parse_qs, urlparse

from requests import RequestException
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    NoTranscriptFound,
    TranscriptsDisabled,
    VideoUnavailable,
    YouTubeTranscriptApiException,
)

logger = logging.getLogger(__name__)

_api = YouTubeTranscriptApi()


def extract_youtube_video_id(url: str) -> str | None:
    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path = parsed.path.strip("/")

    if host.endswith("youtu.be") and path:
        return path.split("/")[0]

    if "youtube.com" in host:
        query_id = parse_qs(parsed.query).get("v", [None])[0]
        if query_id:
            return query_id

        parts = path.split("/")
        for marker in ("shorts", "embed", "live"):
            if marker in parts:
                index = parts.index(marker)
                if len(parts) > index + 1:
                    return parts[index + 1]

    match = re.search(r"(?:v=|youtu\.be/|shorts/|embed/)([A-Za-z0-9_-]{6,})", url)
    return match.group(1) if match else None


def _split_segment(text: str, start: float, duration: float) -> list[dict]:
    tokens = [token.strip() for token in text.split() if token.strip()]
    if not tokens:
        return []

    safe_duration = max(float(duration or 0.0), 0.01)
    token_duration = safe_duration / len(tokens)
    words = []
    for index, token in enumerate(tokens):
        word_start = float(start) + (index * token_duration)
        words.append(
            {
                "text": token,
                "start": word_start,
                "end": word_start + token_duration,
            }
        )
    return words


def fetch_youtube_transcript(
    url: str,
    session_id: str,
    video_id: str,
    max_seconds: float | None = None,
) -> list[dict] | None:
    youtube_id = extract_youtube_video_id(url)
    if not youtube_id:
        logger.info("Could not extract YouTube video ID for Video %s session_id=%s", video_id, session_id)
        return None

    logger.info(
        "Fetching YouTube transcript for Video %s session_id=%s youtube_id=%s max_seconds=%s",
        video_id,
        session_id,
        youtube_id,
        max_seconds if max_seconds is not None else "unlimited",
    )

    try:
        transcript = _api.fetch(youtube_id, languages=("en",))
    except (
        NoTranscriptFound,
        TranscriptsDisabled,
        VideoUnavailable,
        YouTubeTranscriptApiException,
        RequestException,
    ) as exc:
        logger.info(
            "YouTube transcript unavailable for Video %s session_id=%s youtube_id=%s reason=%s",
            video_id,
            session_id,
            youtube_id,
            exc,
        )
        return None

    words: list[dict] = []
    for segment in transcript:
        if max_seconds is not None and segment.start >= max_seconds:
            break
        segment_duration = (
            min(segment.duration, max_seconds - segment.start) if max_seconds is not None else segment.duration
        )
        words.extend(_split_segment(segment.text, segment.start, segment_duration))

    if not words:
        logger.info(
            "YouTube transcript was empty for Video %s session_id=%s youtube_id=%s",
            video_id,
            session_id,
            youtube_id,
        )
        return None

    logger.info(
        "YouTube transcript ready for Video %s session_id=%s youtube_id=%s word_count=%s",
        video_id,
        session_id,
        youtube_id,
        len(words),
    )
    return words
