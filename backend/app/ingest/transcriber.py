from faster_whisper import WhisperModel

from backend.app.core.config import get_settings

_model: WhisperModel | None = None


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        settings = get_settings()
        _model = WhisperModel(settings.whisper_model_size, device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str) -> list[dict]:
    segments, _info = get_model().transcribe(
        audio_path,
        word_timestamps=True,
        vad_filter=True,
        beam_size=1,
    )
    words: list[dict] = []
    for segment in segments:
        if not segment.words:
            continue
        for word in segment.words:
            text = (word.word or "").strip()
            if not text:
                continue
            words.append(
                {
                    "text": text,
                    "start": float(word.start or 0.0),
                    "end": float(word.end or word.start or 0.0),
                }
            )
    return words
