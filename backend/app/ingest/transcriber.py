import logging
from pathlib import Path

from groq import Groq

from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


def get_groq_client() -> Groq:
    settings = get_settings()
    if not settings.groq_api_key:
        raise RuntimeError("GROQ_API_KEY is not configured")
    return Groq(api_key=settings.groq_api_key)


def _response_to_dict(response: object) -> dict:
    if isinstance(response, dict):
        return response
    if hasattr(response, "model_dump"):
        data = response.model_dump()
        extra = getattr(response, "model_extra", None)
        if isinstance(extra, dict):
            data.update(extra)
        return data
    return vars(response)


def _coerce_word(item: dict) -> dict | None:
    text = str(item.get("word") or item.get("text") or "").strip()
    if not text:
        return None
    start = float(item.get("start") or 0.0)
    end = float(item.get("end") or start)
    return {"text": text, "start": start, "end": end}


def _split_text_over_duration(text: str, start: float, end: float) -> list[dict]:
    tokens = [token.strip() for token in text.split() if token.strip()]
    if not tokens:
        return []
    duration = max(end - start, 0.01)
    token_duration = duration / len(tokens)
    return [
        {
            "text": token,
            "start": start + (index * token_duration),
            "end": start + ((index + 1) * token_duration),
        }
        for index, token in enumerate(tokens)
    ]


def _words_from_transcription(response: object) -> list[dict]:
    data = _response_to_dict(response)
    words = [_coerce_word(item) for item in data.get("words", []) if isinstance(item, dict)]
    normalized = [word for word in words if word is not None]
    if normalized:
        return normalized

    segment_words: list[dict] = []
    for segment in data.get("segments", []):
        if not isinstance(segment, dict):
            continue
        text = str(segment.get("text") or "").strip()
        start = float(segment.get("start") or 0.0)
        end = float(segment.get("end") or start)
        segment_words.extend(_split_text_over_duration(text, start, end))
    if segment_words:
        logger.info("Groq transcription returned segment timestamps; approximated word timestamps from segments")
        return segment_words

    text = str(data.get("text") or "").strip()
    if text:
        logger.info("Groq transcription returned text without timestamps; approximated word timestamps")
        return _split_text_over_duration(text, 0.0, 0.01)
    return []


def transcribe(audio_path: str) -> list[dict]:
    settings = get_settings()
    path = Path(audio_path)
    logger.info(
        "Starting Groq transcription path=%s model=%s",
        audio_path,
        settings.groq_transcription_model,
    )
    with path.open("rb") as audio_file:
        response = get_groq_client().audio.transcriptions.create(
            file=audio_file,
            model=settings.groq_transcription_model,
            response_format="verbose_json",
            timestamp_granularities=["word"],
            temperature=0,
        )

    words = _words_from_transcription(response)
    logger.info(
        "Groq transcription complete path=%s model=%s word_count=%s",
        audio_path,
        settings.groq_transcription_model,
        len(words),
    )
    return words
