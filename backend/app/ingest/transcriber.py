import logging
import threading

from faster_whisper import WhisperModel

from backend.app.core.config import get_settings

_model: WhisperModel | None = None
_model_lock = threading.Lock()
logger = logging.getLogger(__name__)


def get_model() -> WhisperModel:
    global _model
    if _model is None:
        with _model_lock:
            if _model is None:
                settings = get_settings()
                logger.info("Loading faster-whisper model size=%s device=cpu compute_type=int8", settings.whisper_model_size)
                _model = WhisperModel(settings.whisper_model_size, device="cpu", compute_type="int8")
    return _model


def transcribe(audio_path: str) -> list[dict]:
    logger.info("Starting transcription path=%s", audio_path)
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
    logger.info("Transcription complete path=%s word_count=%s", audio_path, len(words))
    return words
