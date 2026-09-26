#!/usr/bin/env bash
# Installs the watcher script and its systemd user service, then starts it.
set -euo pipefail
cd "$(dirname "$0")"

install -Dm755 powercut-display-watch "$HOME/.local/bin/powercut-display-watch"
install -Dm644 powercut-display-watch.service "$HOME/.config/systemd/user/powercut-display-watch.service"

systemctl --user daemon-reload
systemctl --user enable --now powercut-display-watch.service
systemctl --user --no-pager status powercut-display-watch.service | head -3
