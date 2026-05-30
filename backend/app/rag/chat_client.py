from collections.abc import Iterator

from groq import Groq

from backend.app.core.config import get_settings

_client: Groq | None = None


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def stream_chat_completion(messages: list[dict]) -> Iterator[str]:
    settings = get_settings()
    stream = get_groq_client().chat.completions.create(
        model=settings.groq_chat_model,
        messages=messages,
        temperature=0.2,
        stream=True,
    )
    for chunk in stream:
        delta = chunk.choices[0].delta.content
        if delta:
            yield delta
