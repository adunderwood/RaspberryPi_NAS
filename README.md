# Raspberry Pi NAS with E-Ink Display

A custom Network Attached Storage (NAS) solution built with a Raspberry Pi 5 and Raspberry Pi Zero 2W, featuring a Pimoroni InkyPHAT e-ink display for real-time system monitoring.

The Raspberry Pi 5 runs the NAS and monitoring service. The Raspberry Pi Zero 2W drives the display and communicates directly with the Pi 5 over a dedicated USB Ethernet gadget connection. Wi-Fi on the Zero can be retained for SSH and maintenance, but is not required for normal display operation.

## 🏗️ Hardware

This project is designed for a 3D-printed NAS case that houses:

- **Raspberry Pi 5** - Main NAS server
- **Raspberry Pi Zero 2W** - Display controller
- **4x 2TB SATA SSDs** - RAID storage
- **Pimoroni InkyPHAT** - E-ink display (212x104 pixels)
- **DS18B20 Temperature Sensor** - Ambient temperature monitoring
- **Cooling Fans** - Active cooling system
- **Data-capable USB-A to Micro-USB cable** - Powers the Pi Zero 2W and provides the dedicated USB Ethernet connection

### Supported Software Configuration

The tested reference configuration uses 64-bit Raspberry Pi OS Bookworm and
Python 3.11 on both Raspberry Pis. The Zero uses gadget address `10.99.0.2`, the
Pi 5 uses `10.99.0.1`, and SSH is enabled on the Zero. Other configurations may
work but are not currently tested or supported.

Normal Zero installation and upgrades are initiated from the Pi 5 with
`nas-monitor deploy-display`. Files and offline Python packages are transferred
over SSH/SCP on the USB gadget connection; the Zero does not require Wi-Fi or
internet access.

**3D Printable Case**: [Thingiverse Thing #7010341](https://www.thingiverse.com/thing:7010341)

## 📊 Features

### Monitoring Service (Pi 5)

- **Unified REST API** - Single service with multiple endpoints
- **Real-time Metrics** - CPU usage, CPU temperature, ambient temperature, RAID status
- **Automatic Log Rotation** - Maintains the last 2000 readings and prevents unbounded log growth
- **Robust Error Handling** - Gracefully handles sensor failures and corrupted data
- **Persistent Storage** - Survives reboots while keeping disk usage minimal

### Display (Pi Zero 2W)

- **E-Ink Dashboard** - Shows disk usage, temperatures, and CPU activity sparkline
- **Visual Warnings** - Switches to red theme when thresholds are exceeded
- **Auto-refresh** - Updates every 5 minutes via cron
- **Configurable Themes** - Light, dark, and red color schemes
- **Dedicated USB Network** - Communicates with the NAS without depending on Wi-Fi, DNS, or mDNS
- **Single-Cable Connection** - The same USB cable powers the Zero and carries Ethernet gadget traffic

## 🚀 Quick Start

> The next-generation SQLite-backed service and installer are currently being
> hardware-tested on the `codex/pi5-foundation` branch. See
> [`docs/hardware-testing.md`](docs/hardware-testing.md) for the public-branch
> deployment and rollback-safe testing workflow.

The corresponding Pi Zero 2W display-agent test is documented in
[`docs/zero-hardware-testing.md`](docs/zero-hardware-testing.md).

### Prerequisites

- Raspberry Pi 5 with Raspberry Pi OS
- Raspberry Pi Zero 2W with Raspberry Pi OS
- Python 3
- Data-capable USB-A to Micro-USB cable between the Pi 5 and Pi Zero 2W
- Wi-Fi or other temporary network access for initial configuration

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/adunderwood/RaspberryPi_NAS.git
   cd RaspberryPi_NAS
   ```

2. **Set up the Raspberry Pi 5 (Monitoring Service)**

   See detailed instructions: [`Raspberry Pi 5/README.md`](Raspberry%20Pi%205/README.md)

   ```bash
   cd "Raspberry Pi 5"
   pip3 install -r requirements.txt
   sudo cp services/nas_service.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable --now nas_service.service
   ```

3. **Set up the Raspberry Pi Zero 2W (Display)**

   See detailed instructions: [`Raspberry Pi Zero 2w/README.md`](Raspberry%20Pi%20Zero%202w/README.md)

   ```bash
   cd "Raspberry Pi Zero 2w"
   # Install Pimoroni libraries and dependencies
   # Configure USB Ethernet gadget mode
   # Configure .env with the dedicated NAS USB address
   # Set up cron job for auto-refresh
   ```

## 🔌 USB Gadget Network

The Pi Zero 2W communicates with the Pi 5 using USB Ethernet gadget mode.

The dedicated network is:

| Device | USB Address |
|--------|-------------|
| Raspberry Pi 5 / NAS | `10.99.0.1/30` |
| Raspberry Pi Zero 2W / Display | `10.99.0.2/30` |

Architecture:

```text
Raspberry Pi 5 / NAS
10.99.0.1
      │
      │ USB-A → Micro-USB
      │ USB Ethernet (g_ether)
      │
10.99.0.2
Raspberry Pi Zero 2W
      │
      └── Pimoroni InkyPHAT
```

The USB cable must be connected to the Zero 2W's **USB/data Micro-USB port**, not the `PWR IN` port. Both ports can power the Zero, but only the USB port provides data connectivity.

Wi-Fi can remain enabled on the Zero for SSH and maintenance. The display itself does not require Wi-Fi once gadget networking is configured.

See the Pi Zero 2W README for complete gadget-mode configuration instructions.

## 📡 API Endpoints

The unified monitoring service runs on port `5000` on the Pi 5.

The display accesses it over the dedicated USB interface:

| Endpoint | Description | Response |
|----------|-------------|----------|
| `http://10.99.0.1:5000/cpu` | CPU usage (last 18 readings) | `{"cpu": [12.5, 15.3, ...]}` |
| `http://10.99.0.1:5000/cpu_temp` | CPU temperature in °C (last 18 readings) | `{"cpu_temp": [45.2, 46.1, ...]}` |
| `http://10.99.0.1:5000/temperature` | Ambient temperature | `{"temperature": "72 F"}` |
| `http://10.99.0.1:5000/raid` | RAID disk usage | `{"total": "5.4T", "used": "2.7T", ...}` |

The service listens on `0.0.0.0:5000`, so it can also be accessed through the Pi 5's normal LAN address when desired.

To verify the service on the Pi 5:

```bash
sudo systemctl status nas_service.service
sudo ss -ltnp | grep ':5000'
curl http://localhost:5000/
```

To verify it from the Pi Zero over USB:

```bash
curl http://10.99.0.1:5000/
```

## 🌡️ DS18B20 Temperature Sensor

The Pi 5 uses a DS18B20 temperature sensor for ambient temperature monitoring.

### GPIO Connections

The important Pi-side connections are:

| Function | Raspberry Pi 5 |
|----------|----------------|
| VCC | Physical Pin 1 - 3.3V |
| Ground | Physical Pin 6 - GND |
| Data | Physical Pin 7 - GPIO4 |

For the BOJACK DS18B20 module used in the original build, the module-to-Pi wiring is:

| Module Wire | Function | Pi Connection |
|-------------|----------|---------------|
| Blue | VCC | Physical Pin 1 - 3.3V |
| Green | Ground | Physical Pin 6 - GND |
| Purple | Data | Physical Pin 7 - GPIO4 |

If using a different DS18B20 module or probe, **do not rely solely on wire colors**. Verify the module's VCC, GND, and DATA markings before connecting it.

Enable 1-Wire by editing:

```bash
sudo nano /boot/firmware/config.txt
```

Add:

```ini
dtoverlay=w1-gpio
```

Reboot and verify:

```bash
sudo reboot
ls /sys/bus/w1/devices/
```

A detected DS18B20 should normally appear as a device beginning with `28-`.

You can read the sensor directly with:

```bash
cat /sys/bus/w1/devices/28-*/w1_slave
```

The value following `t=` is reported in **thousandths of a degree Celsius**. For example:

```text
t=28000
```

means **28.0°C**.

## 🗂️ Project Structure

```text
RaspberryPi_NAS/
├── LICENSE
├── README.md                    # This file
├── Raspberry Pi 5/              # Monitoring service (Pi 5)
│   ├── README.md                # Detailed setup instructions
│   ├── nas_service.py           # Unified monitoring service
│   ├── .env.example             # Configuration template
│   └── services/
│       └── nas_service.service  # Systemd service file
└── Raspberry Pi Zero 2w/        # Display scripts (Pi Zero)
    ├── README.md                # Detailed setup instructions
    ├── nas.py                   # E-ink display script
    ├── display.sh               # Wrapper script for cron
    └── .env.example             # Configuration template
```

## 🔧 Configuration

### Raspberry Pi 5 (Monitoring Service)

Configure via `.env` file:

```bash
LOG_DIR=/home/nas/services      # Log file directory
MAX_LOG_LINES=2000              # Max lines per log (controls size)
LOG_INTERVAL=3                  # Seconds between readings
SAVE_INTERVAL=60                # Seconds between disk writes
TEMP_UNIT=F                     # F or C for ambient temperature
```

The monitoring service should be enabled so that it starts automatically with the NAS:

```bash
sudo systemctl enable --now nas_service.service
```

Verify:

```bash
systemctl status nas_service.service
```

### Raspberry Pi Zero 2W (Display)

Configure via `.env` file:

```bash
# API Endpoints over the dedicated USB gadget network
NAS_URL=http://10.99.0.1:5000/raid
TEMPERATURE_URL=http://10.99.0.1:5000/temperature
CPU_URL=http://10.99.0.1:5000/cpu
CPU_TEMP_URL=http://10.99.0.1:5000/cpu_temp

# Display Settings
THEME=light                     # light, dark, or red
WARN_PERCENT=90                 # Disk usage warning threshold
WARN_TEMP=90                    # Temperature warning threshold (°F)
FONT_DIR=/home/nas/fonts        # Font directory path
```

Before running the display, all four API endpoints can be tested at once:

```bash
for path in raid temperature cpu cpu_temp; do
    echo "=== $path ==="
    curl -sS "http://10.99.0.1:5000/$path"
    echo
done
```

## 🎨 Display Themes

The e-ink display supports three themes:

- **Light** - Black text on white background (default)
- **Dark** - White text on black background
- **Red** - White text on red background (automatically activated on warnings)

The display automatically switches to the red theme when:

- Disk usage exceeds the `WARN_PERCENT` threshold
- Ambient temperature exceeds the `WARN_TEMP` threshold

## 📈 Architecture

### Old System (Before Consolidation)

```text
Pi 5: 7+ separate services on different ports
├── cpu_logger.py → cpu_server.py (port 5002)
├── cpu_temp_logger.py → cpu_temp_server.py (port 5003)
├── therm_logger.py → therm_server.py (port 5000)
└── raid.py (port 5001)
```

### Current System

```text
Pi 5
├── Normal Ethernet → LAN / NAS clients
│
├── nas_service.py (port 5000)
│   ├── Background monitoring threads
│   ├── /cpu
│   ├── /cpu_temp
│   ├── /temperature
│   └── /raid
│
└── USB Ethernet
    └── 10.99.0.1
          │
          │ USB gadget connection
          │
          └── 10.99.0.2
              Pi Zero 2W
                  │
                  └── nas.py → InkyPHAT
```

The Pi Zero fetches monitoring data directly over USB and refreshes the e-ink display every 5 minutes.

Wi-Fi on the Zero is used only for administration and is not part of the normal monitoring path.

**Benefits:**

- ✅ Single monitoring service to manage instead of 7+
- ✅ Dedicated point-to-point connection between NAS and display
- ✅ Display does not depend on Wi-Fi
- ✅ Display does not depend on DNS or mDNS
- ✅ USB cable provides both power and data to the Zero
- ✅ 99% reduction in log file size (100KB vs 35+ MB)
- ✅ Robust error handling
- ✅ Automatic log rotation
- ✅ Simplified deployment

## ⏱️ Display Auto-Refresh

The display is updated every 5 minutes using cron.

Edit the Pi Zero user's crontab:

```bash
crontab -e
```

Add:

```cron
*/5 * * * * /home/nas/display/display.sh >> /home/nas/display/display.log 2>&1
```

This refreshes the display every five minutes and records any errors in `display.log`.

## 🛠️ Troubleshooting

### Monitoring Service Issues

See [`Raspberry Pi 5/README.md`](Raspberry%20Pi%205/README.md#troubleshooting)

### Display Issues

See [`Raspberry Pi Zero 2w/README.md`](Raspberry%20Pi%20Zero%202w/README.md#troubleshooting)

### Common Issues

**Display not updating:**

Verify the monitoring service is running on the Pi 5:

```bash
systemctl status nas_service.service
```

Test the USB API connection from the Zero:

```bash
curl http://10.99.0.1:5000/cpu
```

Check the cron job:

```bash
crontab -l
```

Test the display manually:

```bash
cd ~/display
./display.sh
```

---

**USB connection not working:**

On the Zero, verify that the USB device controller exists:

```bash
ls /sys/class/udc
```

A Pi Zero 2W should normally show something similar to:

```text
3f980000.usb
```

Verify the gadget driver is loaded:

```bash
lsmod | grep -E 'dwc2|g_ether'
```

Verify `usb0` exists:

```bash
ip -br link
```

Check the gadget state:

```bash
cat /sys/class/udc/3f980000.usb/state
```

With the Pi 5 connected and `g_ether` loaded, it should eventually report:

```text
configured
```

If it reports `not attached`:

- Verify the USB cable supports data and is not charge-only.
- Verify the cable is plugged into the Zero's **USB/data** Micro-USB port, not `PWR IN`.
- Verify the USB-A end is connected to the Pi 5.

---

**`usb0` exists but is DOWN after reboot:**

On the Zero:

```bash
sudo nmcli connection up usb-gadget
```

If that restores the connection, verify that the USB gadget network startup service is enabled:

```bash
systemctl status usb-gadget-network.service
```

See the Pi Zero 2W README for setup instructions.

---

**USB network works but monitoring API does not:**

From the Zero:

```bash
ping -c 3 10.99.0.1
curl http://10.99.0.1:5000/
```

If the ping succeeds but port `5000` does not respond, check the Pi 5:

```bash
systemctl status nas_service.service
sudo ss -ltnp | grep ':5000'
```

The service should be listening on:

```text
0.0.0.0:5000
```

---

**InkyPHAT reports GPIO8 / Chip Select already in use:**

If running the display produces:

```text
Woah there, some pins we need are in use!
Chip Select: (line 8, GPIO8) currently claimed by spi0 CS0
```

edit:

```bash
sudo nano /boot/firmware/config.txt
```

and make sure the configuration contains:

```ini
dtparam=spi=on
dtoverlay=spi0-0cs
```

Then reboot.

---

**Temperature sensor not found:**

Verify the wiring:

```text
VCC  → Physical Pin 1 / 3.3V
GND  → Physical Pin 6 / Ground
DATA → Physical Pin 7 / GPIO4
```

Verify that `/boot/firmware/config.txt` contains:

```ini
dtoverlay=w1-gpio
```

Then check:

```bash
ls /sys/bus/w1/devices/
```

A DS18B20 should normally appear with an ID beginning with `28-`.

---

**High memory usage:**

- Reduce `MAX_LOG_LINES` in the monitoring service configuration.
- Increase `LOG_INTERVAL` to collect readings less frequently.

## 📝 License

See [LICENSE](LICENSE) file for details.
