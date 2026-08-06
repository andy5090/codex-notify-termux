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


class TtsTests(unittest.TestCase):
    def test_tts_is_disabled_by_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertFalse(hook.is_tts_enabled(False))

    def test_tts_can_be_enabled_by_flag(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertTrue(hook.is_tts_enabled(True))

    def test_tts_can_be_enabled_by_environment(self) -> None:
        with patch.dict("os.environ", {hook.TTS_ENV_VAR: "yes"}, clear=True):
            self.assertTrue(hook.is_tts_enabled(False))

    @patch("termux_stop_notification.subprocess.Popen")
    @patch("termux_stop_notification.shutil.which", return_value="/bin/termux-tts-speak")
    def test_speak_starts_tts_in_background(self, _which, popen) -> None:
        hook.speak("Done")
        popen.assert_called_once_with(
            ["/bin/termux-tts-speak", "Done"],
            stdout=hook.subprocess.DEVNULL,
            stderr=hook.subprocess.DEVNULL,
            start_new_session=True,
        )

    @patch("termux_stop_notification.subprocess.Popen")
    @patch(
        "termux_stop_notification.shutil.which",
        side_effect=[None, "/bin/termux-tts-speak"],
    )
    def test_tts_runs_when_notification_is_unavailable(self, _which, popen) -> None:
        payload = {"last_assistant_message": "Done"}
        with patch("sys.stdin", io.StringIO(json.dumps(payload))):
            self.assertEqual(hook.main(["--tts"]), 0)
        self.assertEqual(popen.call_args.args[0], ["/bin/termux-tts-speak", "Done"])


if __name__ == "__main__":
    unittest.main()
