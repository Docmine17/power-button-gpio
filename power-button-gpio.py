#!/usr/bin/env python3
"""
GPIO power button monitor.

Watches a GPIO pin for a button press and triggers an action (e.g. a
system shutdown) once the button has been held down for HOLD_TIME
seconds.

Design note: edge events are used only to sleep efficiently between
checks (no busy polling). The button's actual state is always confirmed
with a fresh line.get_value() read rather than inferred from the edge
type. That makes the script resilient to a dropped or missed edge event
(event queue overflow, heavy contact bounce, etc.), which would
otherwise leave the state tracking permanently out of sync with the
real hardware.
"""

import os
import sys
import time
import signal

try:
    import gpiod
except ImportError:
    sys.exit(
        "Error: 'gpiod' module not found.\n"
        "Install it with: sudo apt install python3-libgpiod"
    )

if os.geteuid() != 0:
    sys.exit("Error: this script must be run as root (sudo).")

# --------------------------------------------------------------------------
# Configuration
# --------------------------------------------------------------------------
GPIO_CHIP = "gpiochip1"
GPIO_PIN = 75
HOLD_TIME = 3.0         # seconds the button must be held to trigger the action
DEBOUNCE_TIME = 0.2     # settle time used to filter out contact bounce
POLL_TIMEOUT = 1.0      # max seconds between hardware resyncs while idle/waiting

PRESSED = 0              # pin reads LOW when pressed (pull-up, button to GND)
RELEASED = 1


def signal_handler(sig, frame):
    print("\nMonitoring stopped.")
    sys.exit(0)


signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


class Button:
    """Thin wrapper around a gpiod line for a single push button."""

    def __init__(self, chip_name: str, pin: int):
        self.chip = gpiod.Chip(chip_name)
        try:
            self.line = self.chip.get_line(pin)
            self.line.request(
                consumer="power_button",
                type=gpiod.LINE_REQ_EV_BOTH_EDGES,
                flags=gpiod.LINE_REQ_FLAG_BIAS_PULL_UP,
            )
        except Exception:
            # Don't leak the chip file descriptor if get_line()/request() fails
            # (e.g. the pin is already held by another process).
            self.chip.close()
            raise

    def close(self):
        self.line.release()
        self.chip.close()

    def read(self) -> int:
        """Return the button's current, real hardware state."""
        return self.line.get_value()

    def _drain_events(self):
        """Discard queued edge events so event_wait() blocks properly next time."""
        while self.line.event_wait(sec=0, nsec=0):
            try:
                self.line.event_read()
            except Exception:
                break

    def wait_for_change(self, timeout: float) -> int:
        """
        Sleep until an edge event arrives or `timeout` elapses, then return
        the pin's real value.

        The edge event only wakes us up early; the return value always comes
        from a fresh hardware read, so a missed edge can never leave the
        caller stuck waiting on a state that no longer matches reality.
        """
        sec = int(timeout)
        nsec = int((timeout - sec) * 1_000_000_000)
        self.line.event_wait(sec=sec, nsec=nsec)
        self._drain_events()
        return self.read()

    def read_stable(self, settle_time: float = DEBOUNCE_TIME) -> int:
        """Wait out contact bounce, then return the settled value."""
        time.sleep(settle_time)
        self._drain_events()
        return self.read()


def wait_for_long_press(button: Button, hold_time: float) -> bool:
    """
    Block until the button is either held for `hold_time` seconds (True)
    or released early (False).
    """
    deadline = time.monotonic() + hold_time
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return True

        state = button.wait_for_change(remaining)
        if state == RELEASED and button.read_stable() == RELEASED:
            return False  # released before hold_time was reached


def wait_for_release(button: Button):
    """Block until the button reads RELEASED, resyncing periodically."""
    while button.read() == PRESSED:
        button.wait_for_change(POLL_TIMEOUT)


def main():
    print(f"Monitoring GPIO {GPIO_PIN} on {GPIO_CHIP}.")
    print(f"Hold the button for {HOLD_TIME:.0f}s to trigger the action (Ctrl+C to exit).")

    try:
        button = Button(GPIO_CHIP, GPIO_PIN)
    except Exception as e:
        sys.exit(f"Error: could not acquire GPIO {GPIO_PIN} on {GPIO_CHIP}: {e}")

    try:
        if button.read() == PRESSED:
            print("Note: button is already pressed at startup.")

        while True:
            state = button.wait_for_change(POLL_TIMEOUT)
            if state != PRESSED:
                continue
            if button.read_stable() != PRESSED:
                continue  # bounce/noise, not a real press

            print("\nPress detected, checking hold time...")
            if wait_for_long_press(button, HOLD_TIME):
                print(f"Held for {HOLD_TIME:.0f}s -- triggering action.")
                # os.system("poweroff")  # uncomment to enable shutdown
                print("Waiting for release...")
                wait_for_release(button)
                print("Released. Back to monitoring.\n")
            else:
                print("Short press, ignored.\n")

    finally:
        button.close()


if __name__ == "__main__":
    main()
