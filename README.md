# codex-notify-termux

A small Codex `Stop` hook that displays an Android notification through
Termux:API when Codex finishes a response.

The notification title contains the current project name, and its body contains
a simplified version of the latest Codex response. Notification failures never
affect Codex itself.

## Requirements

- [Termux](https://github.com/termux/termux-app) on Android
- The [Termux:API](https://github.com/termux/termux-api) app and Termux package
- Python 3
- Codex hooks support

Install the required packages in Termux:

```sh
pkg install python termux-api
```

Termux and the Termux:API app must come from the same distribution source to
work together correctly.

## Installation

1. Copy the script into the Codex hooks directory and make it executable:

```sh
mkdir -p "$HOME/.codex/hooks"
cp termux_stop_notification.py "$HOME/.codex/hooks/"
chmod +x "$HOME/.codex/hooks/termux_stop_notification.py"
```

2. Add the following configuration to `~/.codex/config.toml`. Replace `<HOME>`
   with your absolute home path. A typical Termux home path is
   `/data/data/com.termux/files/home`.

```toml
[features]
hooks = true

[[hooks.Stop]]

[[hooks.Stop.hooks]]
type = "command"
command = "/data/data/com.termux/files/usr/bin/python3 <HOME>/.codex/hooks/termux_stop_notification.py"
timeout = 10
statusMessage = "Sending Android completion notification"
```

If a `[features]` section already exists, add `hooks = true` to it instead of
creating a duplicate section. On first use, Codex may ask you to trust the hook.
Review it before approving.

3. Optionally test the hook directly:

```sh
printf '%s' '{"cwd":"/tmp/example","last_assistant_message":"The task is complete."}' \
  | python3 termux_stop_notification.py
```

## Text-to-speech

Text-to-speech is disabled by default. When enabled, the hook reads the same
shortened response used in the notification through Android's system TTS
engine. Speech starts in the background so it does not hold up the Codex
`Stop` hook.

To enable TTS, append `--tts` to the hook command:

```toml
command = "/data/data/com.termux/files/usr/bin/python3 <HOME>/.codex/hooks/termux_stop_notification.py --tts"
```

Remove `--tts` to turn it off again. Because this changes the hook definition,
Codex may ask you to review and trust the hook again.

You can also control TTS without changing the hook definition by setting
`CODEX_TERMUX_TTS` before starting Codex:

```sh
# Enable TTS for Codex processes started from this shell.
export CODEX_TERMUX_TTS=1

# Disable it again.
export CODEX_TERMUX_TTS=0
```

Accepted enabled values are `1`, `true`, `yes`, and `on`, ignoring letter case.
The `--tts` flag always enables speech regardless of the environment variable.

### Choose a voice

List the TTS engines installed on your device:

```sh
termux-tts-engines
```

Select an engine and locale with `--tts-engine`, `--tts-language`, and
`--tts-region`. For example, this configuration uses Google TTS with a Korean
locale, slightly lower pitch, and slightly faster speech:

```toml
command = "/data/data/com.termux/files/usr/bin/python3 <HOME>/.codex/hooks/termux_stop_notification.py --tts --tts-engine com.google.android.tts --tts-language ko --tts-region KR --tts-pitch 0.9 --tts-rate 1.1"
```

Available voice options:

| Option | Meaning | Example |
| --- | --- | --- |
| `--tts-engine` | Engine package reported by `termux-tts-engines` | `com.google.android.tts` |
| `--tts-language` | Language code | `ko` |
| `--tts-region` | Region code | `KR` |
| `--tts-variant` | Engine-specific language variant | Varies by engine |
| `--tts-pitch` | Pitch multiplier; `1.0` is normal | `0.9` |
| `--tts-rate` | Speech-rate multiplier; `1.0` is normal | `1.1` |

Termux:API does not expose a portable option for selecting a specific named
voice, such as a particular male or female voice. Choose that voice in the
Android text-to-speech settings for the selected engine. Engines may ignore an
unsupported language, region, or variant.

You can compare installed engines directly before changing the hook:

```sh
termux-tts-speak -e com.samsung.SMT -l ko -n KR "Samsung voice test"
termux-tts-speak -e com.google.android.tts -l ko -n KR "Google voice test"
```

Installed engine package names vary by device. After changing the hook command,
review and trust its updated definition in Codex when prompted.

## How it works

- Reads the JSON payload supplied through standard input.
- Uses the last component of `cwd` in the notification title.
- Simplifies Markdown in `last_assistant_message` and limits it to 320 characters.
- Optionally reads the shortened response through Android system TTS.
- Uses a stable notification ID so each completion replaces the previous
  notification instead of creating an ever-growing list.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
