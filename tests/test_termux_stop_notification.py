import io
import json
import unittest
from unittest.mock import patch

import termux_stop_notification as hook


class LoadPayloadTests(unittest.TestCase):
    def test_loads_object(self) -> None:
        payload = {"cwd": "/tmp/demo"}
        with patch("sys.stdin", io.StringIO(json.dumps(payload))):
            self.assertEqual(hook.load_payload(), payload)

    def test_rejects_invalid_json(self) -> None:
        with patch("sys.stdin", io.StringIO("not json")):
            self.assertEqual(hook.load_payload(), {})

    def test_rejects_non_object_json(self) -> None:
        with patch("sys.stdin", io.StringIO("[]")):
            self.assertEqual(hook.load_payload(), {})


class SummarizeTests(unittest.TestCase):
    def test_uses_fallback_for_empty_message(self) -> None:
        self.assertEqual(hook.summarize(None), "The task is complete.")

    def test_simplifies_markdown(self) -> None:
        message = "**Done**: [result](https://example.com)\n\n`ok`"
        self.assertEqual(hook.summarize(message), "Done: result ok")

    def test_limits_message_length(self) -> None:
        result = hook.summarize("a" * (hook.MAX_SUMMARY_CHARS + 20))
        self.assertEqual(len(result), hook.MAX_SUMMARY_CHARS)
        self.assertTrue(result.endswith("…"))


if __name__ == "__main__":
    unittest.main()
