from pathlib import Path

from yt_dlp import YoutubeDL

from backend.app.core.config import get_settings


class VideoTooLongError(ValueError):
    pass


def download_audio(url: str, session_id: str, video_id: str, duration_seconds: float) -> str:
    settings = get_settings()
    if duration_seconds and duration_seconds > settings.max_video_seconds:
        raise VideoTooLongError(
            f"Video {video_id} is {duration_seconds:.0f}s; max is {settings.max_video_seconds}s"
        )

    tmp_dir = Path(settings.tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{session_id}_{video_id}"

    opts = {
        "format": "bestaudio/best",
        "outtmpl": str(tmp_dir / f"{prefix}.%(ext)s"),
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
        "postprocessors": [
            {
                "key": "FFmpegExtractAudio",
                "preferredcodec": "mp3",
                "preferredquality": "128",
            }
        ],
    }
    with YoutubeDL(opts) as ydl:
        ydl.download([url])

    candidates = sorted(tmp_dir.glob(f"{prefix}.*"))
    for candidate in candidates:
        if candidate.suffix.lower() in {".mp3", ".m4a", ".webm", ".opus", ".wav"}:
            return str(candidate)
    raise FileNotFoundError(f"Audio download succeeded but no audio file was found for video {video_id}")
