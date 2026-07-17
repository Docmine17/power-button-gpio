# GPIO Power Button Monitoring

A lightweight Python script to monitor a physical power button via GPIO interrupts for use on the Orange Pi Zero 3 running Armbian.

## Features
- **Zero CPU usage**: Uses hardware edge events via `libgpiod` Python bindings instead of constant polling.
- **Self-healing state tracking**: Edge events are only used to wake the script up early — the button's real state is always re-confirmed with a fresh hardware read. This means a missed or dropped edge event (contact bounce, event queue overflow, etc.) can never leave the script stuck thinking the button is still pressed.
- **Accurate startup state**: Reads the actual pin value on startup instead of assuming the button is released, so it behaves correctly even if the script is (re)started while the button is already held down.
- **Debouncing**: Settles and re-checks the pin after every raw transition to ignore physical contact noise.
- **Systemd Service**: Can run as a `systemd` service for automatic startup.

## Hardware Setup
- **Button Wire 1**: Connect to **Physical Pin 12** (PC11 / GPIO 75).
- **Button Wire 2**: Connect to **Physical Pin 9** (GND - Ground).

## Installation

### 1. Requirements
Install the Python 3 `libgpiod` bindings:
```bash
sudo apt update
sudo apt install python3-libgpiod
```

### 2. Manual Testing

Clone the repository (or copy the script) and run it with root privileges:

```bash
sudo python3 power-button-gpio.py
```

Press and hold the button for `HOLD_TIME` seconds (3s by default) to see the trigger message. Short presses or noise are logged and ignored.

### 3. Setup as a Service

To make the script run automatically at boot:

1. Copy the script to a permanent location (e.g., `/usr/local/bin`):
```bash
sudo cp power-button-gpio.py /usr/local/bin/
sudo chmod +x /usr/local/bin/power-button-gpio.py
```

2. Edit `power-button-gpio.service` to ensure the `ExecStart` path points to the new Python script (`/usr/bin/python3 /usr/local/bin/power-button-gpio.py`).
3. Install the service:
```bash
sudo cp power-button-gpio.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now power-button-gpio.service
```

## Configuration

All tunable values live at the top of `power-button-gpio.py`:

| Constant | Default | Meaning |
|---|---|---|
| `GPIO_CHIP` | `gpiochip1` | GPIO chip device |
| `GPIO_PIN` | `75` | Pin number (PC11) |
| `HOLD_TIME` | `3.0` | Seconds the button must be held to trigger the action |
| `DEBOUNCE_TIME` | `0.2` | Settle time used to filter out contact bounce |
| `POLL_TIMEOUT` | `1.0` | Max seconds between hardware resyncs while idle/waiting |

## Enabling Shutdown

By default, the `poweroff` command is commented out in `power-button-gpio.py` for safety during testing:
```python
# os.system("poweroff")  # uncomment to enable shutdown
```
Uncomment that line to enable an actual shutdown once a long press is detected.
