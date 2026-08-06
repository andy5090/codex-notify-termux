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

## How it works

- Reads the JSON payload supplied through standard input.
- Uses the last component of `cwd` in the notification title.
- Simplifies Markdown in `last_assistant_message` and limits it to 320 characters.
- Uses a stable notification ID so each completion replaces the previous
  notification instead of creating an ever-growing list.

## Tests

```sh
python3 -m unittest discover -s tests -v
```

## License

[MIT](LICENSE)
