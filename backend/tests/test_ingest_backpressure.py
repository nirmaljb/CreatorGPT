import asyncio

from backend.app.ingest import pipeline
from backend.app.ingest.extractors import TranscriptResult
from backend.app.ingest.pipeline import process_video_transcript


class DummyProgress:
    async def set_video(self, video_id: str, current_step: str, local_percent: int) -> None:
        return None


def test_process_video_transcript_applies_max_chunks_per_video(monkeypatch) -> None:
    captured_chunks: list[dict] = []

    async def fake_load_or_extract_transcript(video, metadata, cache_entry, progress):
        return TranscriptResult(words=[{"text": "word", "start": 0.0, "end": 1.0}], source="captions")

    def fake_chunk_transcript(words, metadata):
        return [
            {
                "session_id": metadata["session_id"],
                "video_id": metadata["video_id"],
                "chunk_index": index,
                "text": f"chunk {index}",
            }
            for index in range(4)
        ]

    def fake_upsert_chunks(chunks):
        captured_chunks.extend(chunks)
        return len(chunks)

    monkeypatch.setattr("backend.app.ingest.pipeline.load_or_extract_transcript", fake_load_or_extract_transcript)
    monkeypatch.setattr("backend.app.ingest.pipeline.chunk_transcript", fake_chunk_transcript)
    monkeypatch.setattr("backend.app.ingest.pipeline.upsert_chunks", fake_upsert_chunks)
    monkeypatch.setattr("backend.app.ingest.pipeline.update_video_ingest_status", lambda *args, **kwargs: None)
    monkeypatch.setattr("backend.app.ingest.pipeline.record_video_usage", lambda *args, **kwargs: None)
    monkeypatch.setattr(pipeline.get_settings(), "max_chunks_per_video", 2)

    asyncio.run(
        process_video_transcript(
            {"video_id": "A", "platform": "youtube", "url": "https://youtu.be/example123"},
            {
                "session_id": "session-1",
                "video_id": "A",
                "platform": "youtube",
                "cache_key": "cache-1",
                "duration_seconds": 30.0,
            },
            None,
            DummyProgress(),
        )
    )

    assert [chunk["chunk_index"] for chunk in captured_chunks] == [0, 1]
