#!/usr/bin/env python3
"""Show an Android notification through Termux when a Codex turn stops."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


CHANNEL_ID = "codex_high"
MAX_SUMMARY_CHARS = 320
TTS_ENV_VAR = "CODEX_TERMUX_TTS"
TRUTHY_VALUES = {"1", "true", "yes", "on"}


def positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return number


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--tts",
        action="store_true",
        help="read the notification text aloud with Android system TTS",
    )
    parser.add_argument("--tts-engine", help="Android TTS engine package name")
    parser.add_argument("--tts-language", help="TTS language code, for example ko")
    parser.add_argument("--tts-region", help="TTS region code, for example KR")
    parser.add_argument("--tts-variant", help="engine-specific language variant")
    parser.add_argument(
        "--tts-pitch",
        type=positive_float,
        help="voice pitch multiplier (default: 1.0)",
    )
    parser.add_argument(
        "--tts-rate",
        type=positive_float,
        help="speech-rate multiplier (default: 1.0)",
    )
    return parser.parse_args(argv)


def load_payload() -> dict[str, Any]:
    """Read a Codex hook payload from standard input."""
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        return {}
    return payload if isinstance(payload, dict) else {}


def summarize(message: Any) -> str:
    """Turn a Markdown-ish assistant response into notification text."""
    if not isinstance(message, str) or not message.strip():
        return "The task is complete."

    text = re.sub(r"```[^\n]*\n?", " ", message)
    text = re.sub(r"[`*_>#]", "", text)
    text = re.sub(r"\[(.*?)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\s+", " ", text).strip()

    if len(text) <= MAX_SUMMARY_CHARS:
        return text

    shortened = text[: MAX_SUMMARY_CHARS - 1].rsplit(" ", 1)[0].rstrip(" ,.;:")
    return (shortened or text[: MAX_SUMMARY_CHARS - 1]) + "…"


def is_tts_enabled(cli_enabled: bool) -> bool:
    """Return whether TTS is enabled by the CLI flag or environment."""
    env_enabled = os.environ.get(TTS_ENV_VAR, "").strip().lower()
    return cli_enabled or env_enabled in TRUTHY_VALUES


def speak(
    text: str,
    *,
    engine: str | None = None,
    language: str | None = None,
    region: str | None = None,
    variant: str | None = None,
    pitch: float | None = None,
    rate: float | None = None,
) -> None:
    """Start Android system TTS without blocking the Codex Stop hook."""
    termux_tts_speak = shutil.which("termux-tts-speak")
    if termux_tts_speak is None:
        return

    command = [termux_tts_speak]
    for option, value in (
        ("-e", engine),
        ("-l", language),
        ("-n", region),
        ("-v", variant),
        ("-p", pitch),
        ("-r", rate),
    ):
        if value is not None:
            command.extend([option, str(value)])
    command.append(text)

    try:
        subprocess.Popen(
            command,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = load_payload()
    cwd = payload.get("cwd")
    project = Path(cwd).name if isinstance(cwd, str) and cwd else "Codex"
    title = f"Codex complete · {project}"
    content = summarize(payload.get("last_assistant_message"))

    termux_notification = shutil.which("termux-notification")
    if termux_notification is not None:
        try:
            subprocess.run(
                [
                    termux_notification,
                    "--channel",
                    CHANNEL_ID,
                    "--id",
                    "codex-turn-complete",
                    "--title",
                    title,
                    "--content",
                    content,
                    "--priority",
                    "max",
                    "--sound",
                    "--vibrate",
                    "300,150,300",
                ],
                check=False,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=8,
            )
        except (OSError, subprocess.SubprocessError):
            # Notification failures must never change Codex Stop behavior.
            pass

    if is_tts_enabled(args.tts):
        speak(
            content,
            engine=args.tts_engine,
            language=args.tts_language,
            region=args.tts_region,
            variant=args.tts_variant,
            pitch=args.tts_pitch,
            rate=args.tts_rate,
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
