# powercut-display-watch

Automatically switches a laptop + external monitor setup to **mirror mode with laptop speakers** during a power cut, and restores the **extended layout with monitor speakers** when power returns.

Built for Ubuntu (GNOME on Wayland) with PipeWire / WirePlumber audio.

## The problem

Setup: a laptop plus an external monitor over HDMI. The monitor is the primary display in extended mode, and speakers are plugged into the monitor's 3.5 mm jack.

When the power goes out, the monitor dies but the laptop keeps running on battery. The laptop still reports the HDMI port as **connected**, because the HDMI cable carries a little power from the laptop itself. GNOME never notices the monitor is gone, so windows and sound stay on the dead monitor. The only workaround was unplugging the HDMI cable by hand.

## How it works

The monitor and the laptop charger are on the same mains power, so **"charger offline" means "power cut"**. The script checks `/sys/class/power_supply/ACAD/online` every 2 seconds:

| Event | Display | Audio |
|---|---|---|
| Charger goes offline (power cut) | Mirror laptop + monitor | Laptop speakers |
| Charger comes back (power restored) | Extended, monitor primary on the right (after a 5 s delay so the monitor can wake up) | HDMI → monitor speakers |

- The display layout is set with `gdctl`, GNOME's display config tool.
- Audio is switched with `wpctl set-profile`, which changes the sound card profile.
- It runs as a systemd **user** service, so it starts automatically at every login.

## Files

| File | Installed to |
|---|---|
| `powercut-display-watch` | `~/.local/bin/powercut-display-watch` |
| `powercut-display-watch.service` | `~/.config/systemd/user/powercut-display-watch.service` |
| `install.sh` | Copies both files above and enables the service |

## Install

```bash
git clone <your-repo-url> powercut-display-watch
cd powercut-display-watch
./install.sh
```

## Usage

Check that it's running:

```bash
systemctl --user status powercut-display-watch.service
```

Watch it react live (unplug the charger to test):

```bash
journalctl --user -u powercut-display-watch -f
```

Stop and disable it:

```bash
systemctl --user disable --now powercut-display-watch.service
```

## Customising

The settings are at the top of the script and in the two `gdctl set` lines:

| Setting | Current value | How to find yours |
|---|---|---|
| `AC` | `/sys/class/power_supply/ACAD/online` | `ls /sys/class/power_supply/` (look for type `Mains`) |
| `CARD` | `alsa_card.pci-0000_00_1f.3` | `wpctl status`, then `wpctl inspect <device id>` → `device.name` |
| Connectors | `eDP-1` (laptop), `HDMI-1` (monitor) | `/usr/bin/python3 /usr/bin/gdctl show` |
| Extended layout | laptop at scale 1.25, position (0, 362); monitor at scale 1, position (1536, 0), primary | Arrange your displays in Settings → Displays, then read the values from `gdctl show` |
| `RESTORE_DELAY` | `5` seconds | Increase it if your monitor takes longer to wake up |

After editing, run `./install.sh` again.

To dry-run a layout without applying it, add `-V`:

```bash
/usr/bin/python3 /usr/bin/gdctl set -V -L --primary --scale 1.25 -M eDP-1 -M HDMI-1
```

## Notes

- **Unplugging the charger by hand triggers it too.** The laptop can't tell a power cut from a pulled charger.
- **It only acts while you're logged in.** A power cut on the login screen isn't handled.
- **Laptop speaker volume.** The laptop speakers use their own volume setting. Set it once while they're active and it should stay at that level.
- **Why `/usr/bin/python3`?** `gdctl` needs the system Python's `gi` module. A conda or other Python first on `PATH` breaks it, so the script calls the system Python directly.

## Requirements

- GNOME 48+ on Wayland (for `gdctl`)
- PipeWire + WirePlumber (`wpctl`, `pw-dump`)
- systemd user session
