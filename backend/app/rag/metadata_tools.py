from backend.app.rag.prompt import metadata_source_tag
from backend.app.store.postgres import get_video_metadata


def _video_sort_key(video: dict) -> str:
    return str(video.get("video_id") or "")


def _video_by_id(session_id: str, video_id: str) -> dict | None:
    normalized = video_id.upper()
    for video in get_video_metadata(session_id):
        if video["video_id"] == normalized:
            return video
    return None


def get_video_metrics(session_id: str) -> list[dict]:
    return [
        {
            "video_id": video["video_id"],
            "views": video["views"],
            "likes": video["likes"],
            "comments": video["comments"],
            "duration_seconds": video["duration_seconds"],
            "engagement_rate_percent": video["engagement_rate"],
            "source_tag": metadata_source_tag(video["video_id"]),
        }
        for video in sorted(get_video_metadata(session_id), key=_video_sort_key)
    ]


def get_creator_info(session_id: str, video_id: str) -> dict:
    video = _video_by_id(session_id, video_id)
    if video is None:
        return {
            "video_id": video_id.upper(),
            "error": "video_not_found",
            "source_tag": metadata_source_tag(video_id.upper()),
        }
    return {
        "video_id": video["video_id"],
        "creator": video["creator"],
        "creator_followers": video["creator_followers"] if video["creator_followers"] else "unavailable",
        "platform": video["platform"],
        "source_tag": metadata_source_tag(video["video_id"]),
    }


def get_engagement_comparison(session_id: str) -> dict:
    videos = get_video_metrics(session_id)
    ranked = sorted(videos, key=lambda item: item["engagement_rate_percent"], reverse=True)
    winner = ranked[0]["video_id"] if ranked else None
    return {
        "videos": videos,
        "highest_engagement_video_id": winner,
    }


def get_session_video_summary(session_id: str) -> list[dict]:
    return [
        {
            "video_id": video["video_id"],
            "platform": video["platform"],
            "creator": video["creator"],
            "creator_followers": video["creator_followers"] if video["creator_followers"] else "unavailable",
            "views": video["views"],
            "likes": video["likes"],
            "comments": video["comments"],
            "engagement_rate_percent": video["engagement_rate"],
            "duration_seconds": video["duration_seconds"],
            "upload_date": video["upload_date"] or "unknown",
            "hashtags": video["hashtags"],
            "ingest_status": video.get("ingest_status", "unknown"),
            "transcript_source": video.get("transcript_source", "unavailable"),
            "chunk_count": video.get("chunk_count", 0),
            "source_tag": metadata_source_tag(video["video_id"]),
        }
        for video in sorted(get_video_metadata(session_id), key=_video_sort_key)
    ]
