import json
import unittest
from unittest.mock import patch

from backend.app.rag.chat_client import ChatStreamEvent, ChatUsage
from backend.app.rag.service import stream_rag_response


class RagServiceTests(unittest.TestCase):
    def test_stream_includes_route_trace_in_sources_and_done_events(self) -> None:
        state = {
            "route": "HOOK_COMPARISON",
            "retrieval_policy": "hook_retrieval",
            "resolved_query": "Compare the hooks in the first 5 seconds.",
            "metadata": [],
            "metadata_tool_results": [],
            "chunks": [],
            "history": [],
        }

        with (
            patch("backend.app.rag.service.run_retrieval_graph", return_value=state),
            patch("backend.app.rag.service.build_sources", return_value=[]),
            patch("backend.app.rag.service.build_chat_messages", return_value=[]),
            patch(
                "backend.app.rag.service.stream_chat_events",
                return_value=iter(
                    [
                        ChatStreamEvent(token="done", model="llama-test"),
                        ChatStreamEvent(usage=ChatUsage(prompt_tokens=12, completion_tokens=3), model="llama-test"),
                    ]
                ),
            ),
            patch("backend.app.rag.service.append_chat_message"),
            patch("backend.app.rag.service.record_chat_usage") as record_chat_usage,
        ):
            raw_events = list(stream_rag_response("session-1", "Compare hooks"))

        source_payload = json.loads(raw_events[0].split("data: ", 1)[1])
        done_payload = json.loads(raw_events[-1].split("data: ", 1)[1])

        self.assertEqual(source_payload["route"], "HOOK_COMPARISON")
        self.assertEqual(source_payload["retrieval_policy"], "hook_retrieval")
        self.assertEqual(done_payload["route"], "HOOK_COMPARISON")
        self.assertEqual(done_payload["retrieval_policy"], "hook_retrieval")
        record_chat_usage.assert_called_once_with(
            session_id="session-1",
            prompt_tokens=12,
            completion_tokens=3,
            llm_model="llama-test",
        )

    def test_stream_yields_error_event_when_retrieval_fails_before_sources(self) -> None:
        with patch("backend.app.rag.service.run_retrieval_graph", side_effect=RuntimeError("qdrant down")):
            raw_events = list(stream_rag_response("session-1", "Compare hooks"))

        self.assertEqual(len(raw_events), 1)
        error_payload = json.loads(raw_events[0].split("data: ", 1)[1])
        self.assertTrue(raw_events[0].startswith("event: error"))
        self.assertEqual(error_payload["message"], "qdrant down")
        self.assertIsNone(error_payload["route"])


if __name__ == "__main__":
    unittest.main()
