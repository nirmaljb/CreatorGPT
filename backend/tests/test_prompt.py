import unittest

from backend.app.rag.prompt import build_chat_messages


class PromptTests(unittest.TestCase):
    def test_mixed_route_requires_transcript_chunk_citation(self) -> None:
        messages = build_chat_messages(
            query="Why did Video A get more engagement than Video B?",
            metadata=[],
            metadata_tool_results=[],
            chunks=[
                {
                    "video_id": "A",
                    "chunk_index": 0,
                    "start_time": 0.0,
                    "end_time": 5.0,
                    "source_tag": "[Video A, chunk 0, 00:00-00:05]",
                    "is_hook": True,
                    "transcript_source": "captions",
                    "text": "Strong hook.",
                }
            ],
            history=[],
            route="MIXED_COMPARISON",
        )

        user_message = messages[-1]["content"]

        self.assertIn("[ANSWER REQUIREMENTS]", user_message)
        self.assertIn("Cite at least one returned transcript chunk source tag", user_message)

    def test_source_tags_are_rendered_without_source_tag_label(self) -> None:
        messages = build_chat_messages(
            query="What is the engagement rate of each video?",
            metadata=[],
            metadata_tool_results=[
                {
                    "tool": "get_video_metrics",
                    "result": [
                        {
                            "video_id": "A",
                            "engagement_rate_percent": 1.917,
                            "source_tag": "[Video A metadata]",
                        }
                    ],
                }
            ],
            chunks=[],
            history=[],
            route="METADATA_ONLY",
        )

        user_message = messages[-1]["content"]

        self.assertIn("[Video A metadata]", user_message)
        self.assertNotIn("source_tag:", user_message)

    def test_unavailable_metric_flags_are_rendered_as_unavailable(self) -> None:
        messages = build_chat_messages(
            query="What is the engagement rate of each video?",
            metadata=[
                {
                    "video_id": "B",
                    "platform": "instagram",
                    "creator": "Creator B",
                    "creator_followers": 0,
                    "creator_followers_available": False,
                    "views": 0,
                    "views_available": False,
                    "likes": 10,
                    "likes_available": True,
                    "comments": 1,
                    "comments_available": True,
                    "engagement_rate": 0.0,
                    "engagement_rate_available": False,
                    "duration_seconds": 20.0,
                    "upload_date": None,
                    "hashtags": [],
                }
            ],
            metadata_tool_results=[],
            chunks=[],
            history=[],
            route="METADATA_ONLY",
        )

        user_message = messages[-1]["content"]

        self.assertIn("views: unavailable", user_message)
        self.assertIn("creator_followers: unavailable", user_message)
        self.assertIn("engagement_rate_percent: unavailable", user_message)

    def test_hook_route_requirements_are_specific_to_first_five_seconds(self) -> None:
        messages = build_chat_messages(
            query="Compare the hooks in the first 5 seconds.",
            metadata=[],
            metadata_tool_results=[],
            chunks=[
                {
                    "video_id": "B",
                    "chunk_index": 0,
                    "start_time": 0.0,
                    "end_time": 4.0,
                    "source_tag": "[Video B, chunk 0, 00:00-00:04]",
                    "is_hook": True,
                    "transcript_source": "whisper",
                    "text": "Immediate hook.",
                }
            ],
            history=[],
            route="HOOK_COMPARISON",
        )

        self.assertIn("Use only returned chunks marked is_hook true", messages[-1]["content"])

    def test_improvement_route_requires_a_and_b_chunk_evidence(self) -> None:
        messages = build_chat_messages(
            query="Suggest improvements for B based on what worked in A.",
            metadata=[],
            metadata_tool_results=[],
            chunks=[
                {
                    "video_id": "A",
                    "chunk_index": 0,
                    "start_time": 0.0,
                    "end_time": 4.0,
                    "source_tag": "[Video A, chunk 0, 00:00-00:04]",
                    "is_hook": True,
                    "transcript_source": "captions",
                    "text": "Strong hook.",
                },
                {
                    "video_id": "B",
                    "chunk_index": 0,
                    "start_time": 0.0,
                    "end_time": 4.0,
                    "source_tag": "[Video B, chunk 0, 00:00-00:04]",
                    "is_hook": True,
                    "transcript_source": "whisper",
                    "text": "Weak hook.",
                },
            ],
            history=[],
            route="IMPROVEMENT_SUGGESTION",
        )

        user_message = messages[-1]["content"]

        self.assertIn("Video A chunks for evidence of what worked", user_message)
        self.assertIn("Video B chunks for improvement opportunities", user_message)


if __name__ == "__main__":
    unittest.main()
