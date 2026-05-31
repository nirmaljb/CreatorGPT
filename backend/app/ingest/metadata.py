import logging
import re
from datetime import datetime
from urllib.parse import urlparse

from yt_dlp import YoutubeDL

logger = logging.getLogger(__name__)


def _safe_int(value: object) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def _safe_float(value: object) -> float:
    try:
        if value is None:
            return 0.0
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def _platform_from(url: str, extractor_key: str | None) -> str:
    host = urlparse(url).netloc.lower()
    extractor = (extractor_key or "").lower()
    if "youtube" in host or "youtu.be" in host or "youtube" in extractor:
        return "youtube"
    if "instagram" in host or "instagram" in extractor:
        return "instagram"
    return extractor or "unknown"


def _normalize_upload_date(value: str | None) -> str | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y%m%d").date().isoformat()
    except ValueError:
        return value


def _hashtags(info: dict) -> list[str]:
    tags = info.get("tags") or []
    normalized = []
    for tag in tags:
        if not tag:
            continue
        text = str(tag).strip()
        normalized.append(text if text.startswith("#") else f"#{text}")

    text_fields = " ".join(
        str(info.get(field) or "") for field in ("title", "description", "fulltitle")
    )
    for match in re.findall(r"#([\w\d_]+)", text_fields):
        normalized.append(f"#{match}")

    seen = set()
    unique = []
    for tag in normalized:
        key = tag.lower()
        if key not in seen:
            seen.add(key)
            unique.append(tag)
    return unique


def scrape_metadata(url: str, session_id: str, video_id: str, expected_platform: str | None = None) -> dict:
    logger.info(
        "Scraping metadata for Video %s session_id=%s expected_platform=%s url=%s",
        video_id,
        session_id,
        expected_platform or "auto",
        url,
    )
    opts = {
        "quiet": True,
        "no_warnings": True,
        "skip_download": True,
        "noplaylist": True,
    }
    with YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=False)

    views = _safe_int(info.get("view_count"))
    likes = _safe_int(info.get("like_count"))
    comments = _safe_int(info.get("comment_count"))
    engagement_rate = round(((likes + comments) / views) * 100, 4) if views else 0.0

    creator = (
        info.get("uploader")
        or info.get("channel")
        or info.get("creator")
        or info.get("artist")
        or "unknown"
    )
    followers = _safe_int(
        info.get("uploader_subscriber_count")
        or info.get("channel_follower_count")
        or info.get("follower_count")
    )

    platform = _platform_from(url, info.get("extractor_key"))
    metadata = {
        "session_id": session_id,
        "video_id": video_id,
        "url": url,
        "platform": platform,
        "creator": str(creator),
        "creator_followers": followers,
        "views": views,
        "likes": likes,
        "comments": comments,
        "hashtags": _hashtags(info),
        "upload_date": _normalize_upload_date(info.get("upload_date")),
        "duration_seconds": _safe_float(info.get("duration")),
        "engagement_rate": engagement_rate,
    }
    logger.info(
        "Metadata parsed for Video %s session_id=%s platform=%s creator=%s views=%s likes=%s comments=%s duration=%.0fs engagement_rate=%.4f",
        video_id,
        session_id,
        platform,
        metadata["creator"],
        views,
        likes,
        comments,
        metadata["duration_seconds"],
        engagement_rate,
    )
    return metadata
