#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
for tool in python3 xrandr pactl systemctl; do
    command -v "$tool" >/dev/null || { echo "Missing dependency: $tool" >&2; exit 1; }
done
./powercut-display-watch --check
install -Dm755 powercut-display-watch "$HOME/.local/bin/powercut-display-watch"
install -Dm644 powercut-display-watch.service "$HOME/.config/systemd/user/powercut-display-watch.service"
mkdir -p "$HOME/.config/autostart"
cat > "$HOME/.local/bin/powercut-display-watch-session" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
systemctl --user import-environment DISPLAY XAUTHORITY XDG_SESSION_TYPE XDG_CURRENT_DESKTOP
systemctl --user restart powercut-display-watch.service
EOF
chmod 755 "$HOME/.local/bin/powercut-display-watch-session"
cat > "$HOME/.config/autostart/powercut-display-watch.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Powercut Display Watch
Comment=Start power-cut recovery in the Cinnamon desktop session
Exec="$HOME/.local/bin/powercut-display-watch-session"
Terminal=false
X-GNOME-Autostart-enabled=true
EOF
systemctl --user disable powercut-display-watch.service
systemctl --user daemon-reload
systemctl --user enable powercut-display-watch.service
"$HOME/.local/bin/powercut-display-watch-session"
systemctl --user --no-pager status powercut-display-watch.service
