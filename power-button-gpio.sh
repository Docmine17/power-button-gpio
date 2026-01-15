#!/bin/bash

# Run as root!
# Configuration for Orange Pi Zero 3
# Connect: One wire to Physical Pin 12 (PC11/GPIO 75) and other to any GND (like Pin 9)
GPIO_CHIP=1
GPIO_PIN=75

echo "Monitoring GPIO $GPIO_PIN (Physical Pin 12) via interrupts..."
echo "Press the button to test (CTRL+C to exit)."

while true; do
    # Wait for falling edge event (button press)
    if gpiomon --falling --num-events=1 gpiochip$GPIO_CHIP $GPIO_PIN 2>/dev/null; then
        echo "Button press detected!"
        sleep 1
        # poweroff
    else
        echo "Error: GPIO $GPIO_PIN is busy or invalid."
        sleep 5
    fi
done