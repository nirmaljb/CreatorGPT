import json
import unittest
from unittest.mock import patch

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
            patch("backend.app.rag.service.stream_chat_completion", return_value=iter(["done"])),
            patch("backend.app.rag.service.append_chat_message"),
        ):
            raw_events = list(stream_rag_response("session-1", "Compare hooks"))

        source_payload = json.loads(raw_events[0].split("data: ", 1)[1])
        done_payload = json.loads(raw_events[-1].split("data: ", 1)[1])

        self.assertEqual(source_payload["route"], "HOOK_COMPARISON")
        self.assertEqual(source_payload["retrieval_policy"], "hook_retrieval")
        self.assertEqual(done_payload["route"], "HOOK_COMPARISON")
        self.assertEqual(done_payload["retrieval_policy"], "hook_retrieval")


if __name__ == "__main__":
    unittest.main()
