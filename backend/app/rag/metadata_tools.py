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


def _available_value(video: dict, value_key: str, available_key: str) -> object:
    if video.get(available_key, True):
        return video[value_key]
    return "unavailable"


def _engagement_sort_value(video: dict) -> float:
    value = video.get("engagement_rate_percent")
    return value if isinstance(value, int | float) else -1.0


def _raw_interactions(video: dict) -> int | str:
    likes = video.get("likes")
    comments = video.get("comments")
    if isinstance(likes, int) and isinstance(comments, int):
        return likes + comments
    return "unavailable"


def get_video_metrics(session_id: str) -> list[dict]:
    return [
        {
            "video_id": video["video_id"],
            "views": _available_value(video, "views", "views_available"),
            "likes": _available_value(video, "likes", "likes_available"),
            "comments": _available_value(video, "comments", "comments_available"),
            "raw_interactions": _raw_interactions(video),
            "duration_seconds": video["duration_seconds"],
            "engagement_rate_percent": _available_value(
                video,
                "engagement_rate",
                "engagement_rate_available",
            ),
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
        "creator_followers": _available_value(video, "creator_followers", "creator_followers_available"),
        "platform": video["platform"],
        "source_tag": metadata_source_tag(video["video_id"]),
    }


def get_engagement_comparison(session_id: str) -> dict:
    videos = get_video_metrics(session_id)
    unavailable_videos = [
        video["video_id"] for video in videos if not isinstance(video.get("engagement_rate_percent"), int | float)
    ]
    ranked = sorted(videos, key=_engagement_sort_value, reverse=True)
    winner = None if unavailable_videos else ranked[0]["video_id"] if ranked else None
    return {
        "videos": videos,
        "highest_engagement_video_id": winner,
        "comparison_status": "incomplete" if unavailable_videos else "complete",
        "unavailable_engagement_video_ids": unavailable_videos,
        "comparison_note": (
            "Engagement rate comparison is incomplete because at least one video is missing view count metadata."
            if unavailable_videos
            else "Engagement rate comparison is available for both videos."
        ),
    }


def get_session_video_summary(session_id: str) -> list[dict]:
    return [
        {
            "video_id": video["video_id"],
            "platform": video["platform"],
            "creator": video["creator"],
            "creator_followers": _available_value(video, "creator_followers", "creator_followers_available"),
            "views": _available_value(video, "views", "views_available"),
            "likes": _available_value(video, "likes", "likes_available"),
            "comments": _available_value(video, "comments", "comments_available"),
            "engagement_rate_percent": _available_value(
                video,
                "engagement_rate",
                "engagement_rate_available",
            ),
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
