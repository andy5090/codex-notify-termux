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


class CodexSummaryTests(unittest.TestCase):
    def test_codex_summary_is_disabled_by_default(self) -> None:
        with patch.dict("os.environ", {}, clear=True):
            self.assertFalse(hook.is_codex_summary_enabled(False))

    def test_codex_summary_can_be_enabled_by_environment(self) -> None:
        with patch.dict(
            "os.environ", {hook.CODEX_SUMMARY_ENV_VAR: "on"}, clear=True
        ):
            self.assertTrue(hook.is_codex_summary_enabled(False))

    def test_short_single_line_skips_codex(self) -> None:
        self.assertFalse(hook.should_use_codex_summary("Task complete."))

    def test_multiline_text_uses_codex(self) -> None:
        self.assertTrue(hook.should_use_codex_summary("Done.\nTests passed."))

    def test_summary_prompt_bounds_input_and_keeps_tail(self) -> None:
        message = "a" * hook.MAX_CODEX_INPUT_CHARS + "important tail"
        prompt = hook.build_summary_prompt(message)
        self.assertLess(len(prompt), hook.MAX_CODEX_INPUT_CHARS + 1_000)
        self.assertIn("important tail", prompt)

    @patch("termux_stop_notification.request_codex_summary")
    def test_notification_uses_codex_summary(self, request_summary) -> None:
        request_summary.return_value = "작업과 테스트를 완료했습니다."
        result = hook.notification_summary(
            "구현했습니다.\n테스트도 통과했습니다.", codex_enabled=True
        )
        self.assertEqual(result, "작업과 테스트를 완료했습니다.")
        request_summary.assert_called_once_with(
            "구현했습니다.\n테스트도 통과했습니다.",
            model=hook.DEFAULT_SUMMARY_MODEL,
            timeout=hook.DEFAULT_SUMMARY_TIMEOUT,
        )

    @patch("termux_stop_notification.request_codex_summary", return_value=None)
    def test_notification_falls_back_when_app_server_fails(self, _request) -> None:
        message = "**Done.**\nTests passed."
        self.assertEqual(
            hook.notification_summary(message, codex_enabled=True),
            "Done. Tests passed.",
        )


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

    def test_tts_pitch_and_rate_must_be_positive(self) -> None:
        self.assertEqual(hook.parse_args(["--tts-pitch", "0.8"]).tts_pitch, 0.8)
        with patch("sys.stderr", io.StringIO()), self.assertRaises(SystemExit):
            hook.parse_args(["--tts-rate", "0"])

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
    @patch("termux_stop_notification.shutil.which", return_value="/bin/termux-tts-speak")
    def test_speak_passes_voice_options(self, _which, popen) -> None:
        hook.speak(
            "Done",
            engine="com.google.android.tts",
            language="ko",
            region="KR",
            variant="test",
            pitch=0.9,
            rate=1.1,
        )
        self.assertEqual(
            popen.call_args.args[0],
            [
                "/bin/termux-tts-speak",
                "-e",
                "com.google.android.tts",
                "-l",
                "ko",
                "-n",
                "KR",
                "-v",
                "test",
                "-p",
                "0.9",
                "-r",
                "1.1",
                "Done",
            ],
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
