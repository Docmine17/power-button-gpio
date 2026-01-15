# GPIO Power Button Monitoring

A lightweight and efficient project to monitor a physical power button via GPIO interrupts to use on the Orange Pi Zero 3 running Armbian.

## Features
- **Zero CPU usage**: Uses hardware interrupts (via `gpiomon`) instead of constant polling.
- **Robust**: Specifically configured to avoid kernel resource conflicts on the Orange Pi Zero 3.
- **Ready for Production**: Includes a `systemd` service file for automatic startup.

## Hardware Setup
To avoid conflicts with I2C2 and SPI1 (which are common on PC9/GPIO 73), this project uses **Physical Pin 12**.

- **Button Wire 1**: Connect to **Physical Pin 12** (PC11 / GPIO 75).
- **Button Wire 2**: Connect to **Physical Pin 9** (GND - Ground).

## Installation

### 1. Requirements
Install the `libgpiod` utilities:
```bash
sudo apt update && sudo apt install gpiod
```

### 2. Manual Testing
Clone the repository and run the script with root privileges:
```bash
sudo bash power-button-gpio.sh
```
Press the button to see the "Button press detected!" message.

### 3. Setup as a Service
To make the script run automatically at boot:

1. Copy the script to a permanent location (e.g., `/usr/local/bin`):
   ```bash
   sudo cp power-button-gpio.sh /usr/local/bin/
   sudo chmod +x /usr/local/bin/power-button-gpio.sh
   ```

2. Edit `power-button-gpio.service` to update the `ExecStart` path if necessary.

3. Install the service:
   ```bash
   sudo cp power-button-gpio.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable power-button-gpio.service
   sudo systemctl start power-button-gpio.service
   ```

## Enabling Shutdown
By default, the `poweroff` command is commented out in `power-button-gpio.sh` for safety during testing. To enable actual shutdown, uncomment the line:

```bash
# poweroff


