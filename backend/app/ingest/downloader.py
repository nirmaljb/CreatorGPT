import logging
from pathlib import Path

from yt_dlp import YoutubeDL
from yt_dlp.utils import download_range_func

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


def download_audio(url: str, session_id: str, video_id: str, duration_seconds: float) -> str:
    settings = get_settings()
    tmp_dir = Path(settings.effective_tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    prefix = f"{session_id}_{video_id}"
    should_trim = bool(duration_seconds and duration_seconds > settings.max_video_seconds)

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
    if should_trim:
        opts["download_ranges"] = download_range_func(None, [(0, settings.max_video_seconds)])
        opts["force_keyframes_at_cuts"] = True
        logger.info(
            "Video %s session_id=%s is %.0fs; downloading first %ss for Phase 1 transcript",
            video_id,
            session_id,
            duration_seconds,
            settings.max_video_seconds,
        )
    else:
        logger.info(
            "Downloading full audio for Video %s session_id=%s duration=%.0fs",
            video_id,
            session_id,
            duration_seconds,
        )

    with YoutubeDL(opts) as ydl:
        ydl.download([url])

    candidates = sorted(tmp_dir.glob(f"{prefix}.*"))
    for candidate in candidates:
        if candidate.suffix.lower() in {".mp3", ".m4a", ".webm", ".opus", ".wav"}:
            logger.info("Audio ready for Video %s session_id=%s path=%s", video_id, session_id, candidate)
            return str(candidate)
    raise FileNotFoundError(f"Audio download succeeded but no audio file was found for video {video_id}")
