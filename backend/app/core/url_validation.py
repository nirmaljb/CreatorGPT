from urllib.parse import parse_qs, urlparse

from backend.app.core.app_errors import AppError, validation_error


def _field_name(index: int) -> str:
    return f"videos[{index}].url"


def _parse_http_url(raw_url: str) -> tuple[str, object | None]:
    url = raw_url.strip()
    if not url:
        return url, None
    parsed = urlparse(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.netloc:
        return url, None
    return url, parsed


def _host_matches(host: str, root: str) -> bool:
    return host == root or host.endswith(f".{root}")


def _has_path_token(path: str, index: int = 0) -> bool:
    parts = [part for part in path.split("/") if part]
    return len(parts) > index and bool(parts[index].strip())


def is_valid_youtube_url(url: str) -> bool:
    _, parsed = _parse_http_url(url)
    if parsed is None:
        return False

    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    if host == "youtu.be":
        return _has_path_token(path)
    if not _host_matches(host, "youtube.com"):
        return False

    if path.rstrip("/").lower() == "/watch":
        video_ids = parse_qs(parsed.query).get("v") or []
        return any(video_id.strip() for video_id in video_ids)
    parts = [part for part in path.split("/") if part]
    return len(parts) >= 2 and parts[0].lower() == "shorts" and bool(parts[1].strip())


def is_valid_instagram_reel_url(url: str) -> bool:
    _, parsed = _parse_http_url(url)
    if parsed is None:
        return False

    host = (parsed.hostname or "").lower()
    if not _host_matches(host, "instagram.com"):
        return False
    parts = [part for part in (parsed.path or "").split("/") if part]
    return len(parts) >= 2 and parts[0].lower() == "reel" and bool(parts[1].strip())


def validate_video_url(
    platform: str,
    url: str,
    video_id: str | None = None,
    field: str | None = None,
) -> AppError | None:
    normalized_platform = platform.lower().strip()
    trimmed = url.strip()
    if not trimmed:
        return validation_error("Enter a URL for this video.", video_id=video_id, field=field)

    if normalized_platform == "youtube":
        if is_valid_youtube_url(trimmed):
            return None
        if is_valid_instagram_reel_url(trimmed):
            return validation_error(
                "Selected platform is YouTube, but the URL is an Instagram Reel.",
                video_id=video_id,
                field=field,
                code="VALIDATION_PLATFORM_URL_MISMATCH",
            )
        return validation_error(
            "Enter a supported YouTube URL: youtube.com/watch, youtube.com/shorts, or youtu.be.",
            video_id=video_id,
            field=field,
        )

    if normalized_platform == "instagram":
        if is_valid_instagram_reel_url(trimmed):
            return None
        if is_valid_youtube_url(trimmed):
            return validation_error(
                "Selected platform is Instagram, but the URL is a YouTube video.",
                video_id=video_id,
                field=field,
                code="VALIDATION_PLATFORM_URL_MISMATCH",
            )
        return validation_error(
            "Enter a supported Instagram Reel URL in the form instagram.com/reel/...",
            video_id=video_id,
            field=field,
        )

    return validation_error(
        "Unsupported video platform.",
        video_id=video_id,
        field=field,
        code="VALIDATION_UNSUPPORTED_PLATFORM",
    )


def validate_ingest_videos(videos: list[dict]) -> tuple[list[dict], AppError | None]:
    normalized: list[dict] = []
    for index, video in enumerate(videos):
        video_id = str(video.get("video_id") or ("A" if index == 0 else "B"))
        platform = str(video.get("platform") or "").lower().strip()
        url = str(video.get("url") or "").strip()
        error = validate_video_url(platform, url, video_id=video_id, field=_field_name(index))
        if error is not None:
            return [], error
        normalized.append({**video, "video_id": video_id, "platform": platform, "url": url})
    return normalized, None
