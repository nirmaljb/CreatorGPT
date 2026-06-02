import math
from collections.abc import Iterator
from dataclasses import dataclass

from groq import Groq

from backend.app.core.config import get_settings

_client: Groq | None = None


@dataclass(frozen=True)
class ChatUsage:
    prompt_tokens: int
    completion_tokens: int


@dataclass(frozen=True)
class ChatStreamEvent:
    token: str = ""
    usage: ChatUsage | None = None
    model: str | None = None


def get_groq_client() -> Groq:
    global _client
    if _client is None:
        settings = get_settings()
        if not settings.groq_api_key:
            raise RuntimeError("GROQ_API_KEY is not configured")
        _client = Groq(api_key=settings.groq_api_key)
    return _client


def _usage_value(usage: object, key: str) -> int:
    if isinstance(usage, dict):
        return int(usage.get(key) or 0)
    return int(getattr(usage, key, 0) or 0)


def _usage_from_chunk(chunk: object) -> ChatUsage | None:
    usage = getattr(chunk, "usage", None)
    if usage is None:
        return None
    return ChatUsage(
        prompt_tokens=_usage_value(usage, "prompt_tokens"),
        completion_tokens=_usage_value(usage, "completion_tokens"),
    )


def estimate_text_tokens(text: str) -> int:
    if not text:
        return 0
    return max(1, math.ceil(len(text) / 4))


def estimate_message_tokens(messages: list[dict]) -> int:
    serialized = "\n".join(f"{item.get('role', '')}: {item.get('content', '')}" for item in messages)
    return estimate_text_tokens(serialized)


def stream_chat_events(messages: list[dict]) -> Iterator[ChatStreamEvent]:
    settings = get_settings()
    stream = get_groq_client().chat.completions.create(
        model=settings.groq_chat_model,
        messages=messages,
        temperature=0.2,
        stream=True,
    )
    for chunk in stream:
        usage = _usage_from_chunk(chunk)
        if usage:
            yield ChatStreamEvent(usage=usage, model=getattr(chunk, "model", None) or settings.groq_chat_model)

        choices = getattr(chunk, "choices", []) or []
        if not choices:
            continue
        delta = getattr(choices[0].delta, "content", None)
        if delta:
            yield ChatStreamEvent(token=delta, model=getattr(chunk, "model", None) or settings.groq_chat_model)


def stream_chat_completion(messages: list[dict]) -> Iterator[str]:
    for event in stream_chat_events(messages):
        if event.token:
            yield event.token
