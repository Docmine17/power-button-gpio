#!/bin/bash

# Run as root!
# Configuration for Orange Pi Zero 3
# Connect: One wire to Physical Pin 12 (PC11/GPIO 75) and other to any GND (like Pin 9)
GPIO_CHIP=1
GPIO_PIN=75
HOLD_TIME=3 # Seconds to hold the button

echo "Monitoring GPIO $GPIO_PIN (Physical Pin 12) via interrupts..."
echo "Press and hold the button for ${HOLD_TIME}s to trigger action (CTRL+C to exit)."

while true; do
    # Wait for falling edge event (button press) using hardware interrupts
    if gpiomon --falling --num-events=1 gpiochip$GPIO_CHIP $GPIO_PIN 2>/dev/null; then
        echo "Signal detected! Verifying if it's a long press..."

        STILL_PRESSED=true
        # Check the pin state multiple times during the HOLD_TIME period
        # We check every 100ms (0.1s)
        for ((i=1; i<=$((HOLD_TIME * 10)); i++)); do
            sleep 0.1
            # gpioget returns 0 if the button is still connected to GND
            if [ "$(gpioget gpiochip$GPIO_CHIP $GPIO_PIN)" -ne 0 ]; then
                STILL_PRESSED=false
                break
            fi
        done

        if [ "$STILL_PRESSED" = true ]; then
            echo "Button held for ${HOLD_TIME}s. Action triggered!"
            # poweroff
        else
            echo "Short press or noise detected. Ignoring..."
        fi

        # Avoid immediate re-triggering and let the button be released
        sleep 1
    else
        echo "Error: GPIO $GPIO_PIN is busy or invalid."
        sleep 5
    fi
done
