#!/usr/bin/env python3
"""Show an Android notification through Termux when a Codex turn stops."""

from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


CHANNEL_ID = "codex_high"
MAX_SUMMARY_CHARS = 320


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


def main() -> int:
    payload = load_payload()
    cwd = payload.get("cwd")
    project = Path(cwd).name if isinstance(cwd, str) and cwd else "Codex"
    title = f"Codex complete · {project}"
    content = summarize(payload.get("last_assistant_message"))

    termux_notification = shutil.which("termux-notification")
    if termux_notification is None:
        return 0

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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
