from pathlib import Path

from yt_dlp.utils import DownloadError

from backend.app.ingest.chunker import chunk_transcript
from backend.app.ingest.downloader import VideoTooLongError, download_audio
from backend.app.ingest.metadata import scrape_metadata
from backend.app.ingest.transcriber import transcribe
from backend.app.store.postgres import update_session_status, upsert_video_metadata
from backend.app.store.vector import upsert_chunks


def ingest_session(session_id: str, youtube_url: str, instagram_url: str) -> None:
    audio_paths: list[str] = []
    try:
        update_session_status(session_id, "processing")
        for video_id, url in (("A", youtube_url), ("B", instagram_url)):
            metadata = scrape_metadata(url, session_id=session_id, video_id=video_id)
            upsert_video_metadata(metadata)

            audio_path = download_audio(
                url,
                session_id=session_id,
                video_id=video_id,
                duration_seconds=metadata["duration_seconds"],
            )
            audio_paths.append(audio_path)

            words = transcribe(audio_path)
            chunks = chunk_transcript(words, metadata)
            upsert_chunks(chunks)

        update_session_status(session_id, "ready")
    except DownloadError as exc:
        update_session_status(session_id, "failed", f"Video download/extraction failed: {exc}")
    except VideoTooLongError as exc:
        update_session_status(session_id, "failed", str(exc))
    except Exception as exc:
        update_session_status(session_id, "failed", f"Ingestion failed: {exc}")
    finally:
        for audio_path in audio_paths:
            try:
                Path(audio_path).unlink(missing_ok=True)
            except OSError:
                pass
