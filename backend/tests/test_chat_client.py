from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from backend.app.rag.chat_client import (
    ChatUsage,
    estimate_message_tokens,
    estimate_text_tokens,
    stream_chat_events,
)


def test_stream_chat_events_yields_tokens_and_usage() -> None:
    token_chunk = SimpleNamespace(
        choices=[SimpleNamespace(delta=SimpleNamespace(content="hello"))],
        usage=None,
        model="llama-test",
    )
    usage_chunk = SimpleNamespace(
        choices=[],
        usage=SimpleNamespace(prompt_tokens=20, completion_tokens=5),
        model="llama-test",
    )
    create = MagicMock(return_value=iter([token_chunk, usage_chunk]))
    client = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=create)))

    with (
        patch("backend.app.rag.chat_client.get_groq_client", return_value=client),
        patch("backend.app.rag.chat_client.get_settings") as get_settings,
    ):
        get_settings.return_value.groq_chat_model = "llama-test"
        events = list(stream_chat_events([{"role": "user", "content": "hi"}]))

    assert events[0].token == "hello"
    assert events[0].model == "llama-test"
    assert events[1].usage == ChatUsage(prompt_tokens=20, completion_tokens=5)
    create.assert_called_once()
    assert create.call_args.kwargs["stream"] is True


def test_token_estimates_are_nonzero_for_text() -> None:
    assert estimate_text_tokens("") == 0
    assert estimate_text_tokens("hello") >= 1
    assert estimate_message_tokens([{"role": "user", "content": "hello"}]) >= 1
