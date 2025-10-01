# Raspberry Pi NAS with E-Ink Display

A custom Network Attached Storage (NAS) solution built with Raspberry Pi 5 and Raspberry Pi Zero 2W, featuring a Pimoroni InkyPHAT e-ink display for real-time system monitoring.

## 🏗️ Hardware

This project is designed for a 3D-printed NAS case that houses:

- **Raspberry Pi 5** - Main NAS server
- **Raspberry Pi Zero 2W** - Display controller
- **4x 2TB SATA SSDs** - RAID storage
- **Pimoroni InkyPHAT** - E-ink display (212x104 pixels)
- **DS18B20 Temperature Sensor** - Ambient temperature monitoring
- **Cooling Fans** - Active cooling system

**3D Printable Case**: [Thingiverse Thing #7010341](https://www.thingiverse.com/thing:7010341)

## 📊 Features

### Monitoring Service (Pi 5)
- **Unified REST API** - Single service with multiple endpoints
- **Real-time Metrics** - CPU usage, CPU temperature, ambient temperature, RAID status
- **Automatic Log Rotation** - Maintains last 2000 readings, prevents unbounded log growth
- **Robust Error Handling** - Gracefully handles sensor failures and corrupted data
- **Persistent Storage** - Survives reboots while keeping disk usage minimal

### Display (Pi Zero 2W)
- **E-Ink Dashboard** - Shows disk usage, temperatures, CPU activity sparkline
- **Visual Warnings** - Switches to red theme when thresholds exceeded
- **Auto-refresh** - Updates every 5 minutes via cron
- **Configurable Themes** - Light, dark, and red color schemes

## 🚀 Quick Start

### Prerequisites
- Raspberry Pi 5 with Raspberry Pi OS
- Raspberry Pi Zero 2W with Raspberry Pi OS
- Python 3.7+
- Network connectivity between the Pis

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/RaspberryPi_NAS.git
   cd RaspberryPi_NAS
   ```

2. **Set up the Raspberry Pi 5 (Monitoring Service)**

   See detailed instructions: [`Raspberry Pi 5/README.md`](Raspberry%20Pi%205/README.md)

   ```bash
   cd "Raspberry Pi 5"
   pip3 install -r requirements.txt
   sudo cp services/nas_service.service /etc/systemd/system/
   sudo systemctl enable nas_service
   sudo systemctl start nas_service
   ```

3. **Set up the Raspberry Pi Zero 2W (Display)**

   See detailed instructions: [`Raspberry Pi Zero 2w/README.md`](Raspberry%20Pi%20Zero%202w/README.md)

   ```bash
   cd "Raspberry Pi Zero 2w"
   # Install Pimoroni libraries and dependencies
   # Configure .env with your NAS endpoint
   # Set up cron job for auto-refresh
   ```

## 📡 API Endpoints

The unified monitoring service runs on the Pi 5 and provides:

| Endpoint | Description | Response |
|----------|-------------|----------|
| `http://nas.local:5000/cpu` | CPU usage (last 18 readings) | `{"cpu": [12.5, 15.3, ...]}` |
| `http://nas.local:5000/cpu_temp` | CPU temperature in °C (last 18) | `{"cpu_temp": [45.2, 46.1, ...]}` |
| `http://nas.local:5000/temperature` | Ambient temperature | `{"temperature": "72 F"}` |
| `http://nas.local:5000/raid` | RAID disk usage | `{"total": "1.8T", "used": "900G", ...}` |

## 🗂️ Project Structure

```
RaspberryPi_NAS/
├── LICENSE
├── README.md                    # This file
├── Raspberry Pi 5/              # Monitoring service (Pi 5)
│   ├── README.md               # Detailed setup instructions
│   ├── nas_service.py          # Unified monitoring service
│   ├── .env.example            # Configuration template
│   └── services/
│       └── nas_service.service # Systemd service file
└── Raspberry Pi Zero 2w/        # Display scripts (Pi Zero)
    ├── README.md               # Detailed setup instructions
    ├── nas.py                  # E-ink display script
    ├── display.sh              # Wrapper script for cron
    └── .env.example            # Configuration template
```

## 🔧 Configuration

### Raspberry Pi 5 (Monitoring Service)

Configure via `.env` file:
```bash
LOG_DIR=/home/nas/services      # Log file directory
MAX_LOG_LINES=2000              # Max lines per log (controls size)
LOG_INTERVAL=3                  # Seconds between readings
SAVE_INTERVAL=60                # Seconds between disk writes
TEMP_UNIT=F                     # F or C for ambient temp
```

### Raspberry Pi Zero 2W (Display)

Configure via `.env` file:
```bash
# API Endpoints (all served from unified service)
NAS_URL=http://nas.local:5000/raid
TEMPERATURE_URL=http://nas.local:5000/temperature
CPU_URL=http://nas.local:5000/cpu
CPU_TEMP_URL=http://nas.local:5000/cpu_temp

# Display Settings
THEME=light                     # light, dark, or red
WARN_PERCENT=90                 # Disk usage warning threshold
WARN_TEMP=90                    # Temperature warning threshold (°F)
FONT_DIR=/home/nas/fonts        # Font directory path
```

## 🎨 Display Themes

The e-ink display supports three themes:
- **Light** - Black text on white background (default)
- **Dark** - White text on black background
- **Red** - White text on red background (automatically activated on warnings)

The display automatically switches to the red theme when:
- Disk usage exceeds `WARN_PERCENT` threshold
- Ambient temperature exceeds `WARN_TEMP` threshold

## 📈 Architecture

### Old System (Before Consolidation)
```
Pi 5: 7+ separate services on different ports
├── cpu_logger.py → cpu_server.py (port 5002)
├── cpu_temp_logger.py → cpu_temp_server.py (port 5003)
├── therm_logger.py → therm_server.py (port 5000)
└── raid.py (port 5001)
```

### New System (Unified)
```
Pi 5: 1 unified service on port 5000
└── nas_service.py
    ├── Background threads (loggers)
    └── Flask API (4 endpoints)

Pi Zero: 1 display script (cron)
└── nas.py (updates every 5 min)
```

**Benefits:**
- ✅ Single service to manage (vs 7+)
- ✅ 99% reduction in log file size (100KB vs 35+ MB)
- ✅ Robust error handling
- ✅ Automatic log rotation
- ✅ Simplified deployment

## 🛠️ Troubleshooting

### Monitoring Service Issues
See [`Raspberry Pi 5/README.md`](Raspberry%20Pi%205/README.md#troubleshooting)

### Display Issues
See [`Raspberry Pi Zero 2w/README.md`](Raspberry%20Pi%20Zero%202w/README.md#troubleshooting)

### Common Issues

**Display not updating:**
- Verify monitoring service is running: `systemctl status nas_service`
- Test API endpoints: `curl http://nas.local:5000/cpu`
- Check cron job: `crontab -l`

**Temperature sensor not found:**
- Enable 1-Wire in `/boot/config.txt`: `dtoverlay=w1-gpio`
- Verify sensor: `ls /sys/bus/w1/devices/`

**High memory usage:**
- Reduce `MAX_LOG_LINES` in monitoring service config
- Decrease `LOG_INTERVAL` to collect less frequently

## 📝 License

See [LICENSE](LICENSE) file for details.
