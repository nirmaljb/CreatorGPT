import hashlib
import json

from backend.app.core.config import get_settings

CACHE_VERSION = "extract-v3"
SESSION_METADATA_KEYS = {
    "session_id",
    "video_id",
    "ingest_status",
    "video_error_message",
    "chunk_count",
    "cache_key",
    "metadata_cached",
    "transcript_cached",
}


def sanitize_json(value: object) -> object:
    return json.loads(json.dumps(value, default=str))


def normalized_url(url: str) -> str:
    return url.strip()


def extraction_cache_key(platform: str, url: str, max_video_seconds: int | None = None) -> str:
    settings = get_settings()
    payload = {
        "version": CACHE_VERSION,
        "platform": platform.lower().strip(),
        "url": normalized_url(url),
        "max_video_seconds": max_video_seconds if max_video_seconds is not None else settings.max_video_seconds,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def metadata_for_cache(metadata: dict) -> dict:
    return {
        key: sanitize_json(value)
        for key, value in metadata.items()
        if key not in SESSION_METADATA_KEYS and key != "raw_metadata"
    }


def metadata_from_cache(
    cached_metadata: dict,
    session_id: str,
    video_id: str,
    url: str,
    cache_key: str,
    raw_metadata: dict | None,
    transcript_source: str,
    transcript_cached: bool,
) -> dict:
    metadata = dict(cached_metadata)
    metadata.update(
        {
            "session_id": session_id,
            "video_id": video_id,
            "url": url,
            "raw_metadata": raw_metadata,
            "ingest_status": "metadata_ready",
            "video_error_message": None,
            "transcript_source": transcript_source,
            "chunk_count": 0,
            "cache_key": cache_key,
            "metadata_cached": True,
            "transcript_cached": transcript_cached,
        }
    )
    return metadata


def failed_video_metadata(
    session_id: str,
    video_id: str,
    platform: str,
    url: str,
    cache_key: str,
    error_message: str,
) -> dict:
    return {
        "session_id": session_id,
        "video_id": video_id,
        "url": url,
        "platform": platform,
        "creator": "unknown",
        "creator_followers": 0,
        "views": 0,
        "likes": 0,
        "comments": 0,
        "hashtags": [],
        "upload_date": None,
        "duration_seconds": 0.0,
        "engagement_rate": 0.0,
        "raw_metadata": None,
        "ingest_status": "failed",
        "video_error_message": error_message,
        "transcript_source": "unavailable",
        "chunk_count": 0,
        "cache_key": cache_key,
        "metadata_cached": False,
        "transcript_cached": False,
    }
