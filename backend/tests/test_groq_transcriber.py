import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, mock_open, patch

from backend.app.ingest import transcriber


class GroqTranscriberTests(unittest.TestCase):
    def test_words_from_groq_word_timestamps(self) -> None:
        response = {
            "text": "hello world",
            "words": [
                {"word": "hello", "start": 0.0, "end": 0.5},
                {"word": "world", "start": 0.5, "end": 1.0},
            ],
        }

        self.assertEqual(
            transcriber._words_from_transcription(response),
            [
                {"text": "hello", "start": 0.0, "end": 0.5},
                {"text": "world", "start": 0.5, "end": 1.0},
            ],
        )

    def test_words_from_groq_segments_when_word_timestamps_missing(self) -> None:
        response = {"segments": [{"text": "hello world", "start": 2.0, "end": 4.0}]}

        words = transcriber._words_from_transcription(response)

        self.assertEqual([word["text"] for word in words], ["hello", "world"])
        self.assertEqual(words[0]["start"], 2.0)
        self.assertEqual(words[-1]["end"], 4.0)

    def test_transcribe_uses_groq_whisper_large_v3(self) -> None:
        create = MagicMock(return_value={"words": [{"word": "hello", "start": 0.0, "end": 0.5}]})
        client = SimpleNamespace(audio=SimpleNamespace(transcriptions=SimpleNamespace(create=create)))

        with (
            patch("backend.app.ingest.transcriber.get_groq_client", return_value=client),
            patch("pathlib.Path.open", mock_open(read_data=b"audio")),
            patch("backend.app.ingest.transcriber.get_settings") as get_settings,
        ):
            get_settings.return_value.groq_transcription_model = "whisper-large-v3"
            words = transcriber.transcribe("/tmp/audio.mp3")

        self.assertEqual(words, [{"text": "hello", "start": 0.0, "end": 0.5}])
        create.assert_called_once()
        kwargs = create.call_args.kwargs
        self.assertEqual(kwargs["model"], "whisper-large-v3")
        self.assertEqual(kwargs["response_format"], "verbose_json")
        self.assertEqual(kwargs["timestamp_granularities"], ["word"])


if __name__ == "__main__":
    unittest.main()
