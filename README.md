# powercut-display-watch — Linux Mint

Power-cut recovery for **Linux Mint 22.3, Cinnamon on X11**, using
`xrandr` and `pactl` (PulseAudio or PipeWire's PulseAudio compatibility server).
This version replaces the original GNOME/Wayland-specific setup.

The laptop charger and external monitor must share mains power. Unplugging the
charger manually also triggers recovery.

* On battery: enable the laptop screen at (0, 0), make it primary, disable
  external displays, use connected headphones or fall back to the built-in speakers, and move playing audio.
  Disabling the dead display keeps windows accessible on the laptop.
* On AC: wait five seconds for the monitor, then restore the display positions,
  resolutions, refresh rates, rotations and primary display captured before the
  outage. Select headphones first, then available monitor speakers, then laptop speakers.
  Move playing audio to the selected output.
* Detect the charger's `Mains` power supply automatically (`ADP0` on this laptop).
* Check audio connections every two seconds, including while already on AC.
  Wired headphones must report their jack as available. Bluetooth headphones
  are recognized by headset/headphone device metadata. The FANTECH FUSION USB
  headset is explicitly recognized because it reports its port as “Speakers”.
* Retry failed recovery operations and wait for disconnected monitors to return.
* Keep the outage snapshot under `~/.local/state/powercut-display-watch/` so
  a watcher restart during an outage does not lose the normal layout.

## Install

Run inside your Cinnamon desktop session, without sudo:

```bash
./install.sh
```

The installer checks the live setup before changing files. It installs the
watcher in `~/.local/bin`, a systemd user service, and a Cinnamon-compatible
login entry in `~/.config/autostart/powercut-display-watch.desktop`. The login
entry imports the desktop's X11 environment and restarts the user service.
No additional packages are needed on this system.

## Check and test

```bash
./powercut-display-watch --check   # Read-only live configuration check
python3 test_watch.py             # Regression tests
systemctl --user status powercut-display-watch.service
journalctl --user -u powercut-display-watch.service -f
```

Unplug the laptop charger while keeping the external display attached. The
laptop screen and speakers should take over within about two seconds. Reconnect
the charger; the prior arrangement should return after approximately five
seconds, or later if the monitor needs more time to reconnect.

The `--check` command is read-only and also prints the preferred audio output.
On startup, the service applies the audio priority without changing the AC display layout.
A saved, unfinished outage is recovered after a restart on AC.

## Configuration

Optional environment variables (set via `systemctl --user edit
powercut-display-watch.service`, under `[Service]` with `Environment=...`):

* `POWERCUT_AC`: override the detected charger `online` file.
* `POWERCUT_CARD`: built-in sound card; default `alsa_card.pci-0000_00_1f.3`.
* `POWERCUT_HEADPHONE_MATCH`: extra device-name match for USB headphones that
  report themselves as speakers; default `FANTECH_FUSION`. Generic USB speakers
  are not automatically classified as headphones.
* `POWERCUT_RESTORE_DELAY`: monitor wake-up delay in seconds; default `5`.

This setup expects an eDP or LVDS laptop screen and standard analog speaker
profiles. Arbitrary Xrandr scaling/transforms and multi-user concurrent graphical
sessions are outside this version's scope. It runs while your user session is
active, not on the login screen.

## Disable

```bash
systemctl --user disable --now powercut-display-watch.service
mv ~/.config/autostart/powercut-display-watch.desktop \
   ~/.config/autostart/powercut-display-watch.desktop.disabled
```

Both steps are needed because Cinnamon's login entry also starts the service.
