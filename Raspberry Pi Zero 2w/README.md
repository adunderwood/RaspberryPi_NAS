# NAS Display

A Python script that displays NAS system information on a Pimoroni InkyPHAT e-ink display for Raspberry Pi Zero.

## Features

- **Disk Usage**: Shows total, used, and free space with percentage
- **CPU Metrics**: Real-time CPU usage sparkline chart
- **Temperature Monitoring**: Displays both ambient and CPU temperature
- **Visual Warnings**: Automatically switches to red theme when disk usage or temperature exceeds thresholds
- **Configurable Themes**: Light, dark, and red color schemes

## Hardware Requirements

- Raspberry Pi Zero (or compatible)
- Pimoroni InkyPHAT display
- NAS server with API endpoints

## Installation

### 1. Install Dependencies

```bash
# Create and activate virtual environment
python3 -m venv ~/.virtualenvs/pimoroni
source ~/.virtualenvs/pimoroni/bin/activate

# Install required packages
pip install -r requirements.txt
```

Or install manually:
```bash
pip install inky pillow requests python-dotenv sparklines font-fredoka-one
```

### 2. Configure Environment Variables

Copy the example `.env` file and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```bash
# API Endpoints (Unified NAS Service on port 5000)
NAS_URL=http://nas.local:5000/raid
TEMPERATURE_URL=http://nas.local:5000/temperature
CPU_URL=http://nas.local:5000/cpu
CPU_TEMP_URL=http://nas.local:5000/cpu_temp

# Display Settings
MESSAGE=Bunny NAS
THEME=light                # Options: light, dark, red
WARN_PERCENT=90           # Disk usage warning threshold (%)
WARN_TEMP=90              # Temperature warning threshold (°F)

# Font Directory
FONT_DIR=/home/nas/fonts
```

### 3. Set Up Automatic Updates

The `display.sh` script handles virtualenv activation and script execution:

```bash
#!/bin/bash
source ~/.virtualenvs/pimoroni/bin/activate
python /home/nas/display/nas.py
```

Make it executable:
```bash
chmod +x display.sh
```

Add to crontab to update every 5 minutes:
```bash
crontab -e
```

Add this line:
```
*/5 * * * * /home/nas/display/display.sh
```

## API Endpoints

The script expects JSON responses from the following endpoints.

**Note**: As of the unified NAS service, all endpoints are served from a single service on port 5000. See `../Raspberry Pi 5/README.md` for the unified service documentation.

### Disk Info (`NAS_URL`)
```json
{
  "total": "1.0 TB",
  "used": "500 GB",
  "free": "500 GB",
  "percent": "50%"
}
```

### Temperature (`TEMPERATURE_URL`)
```json
{
  "temperature": "72 F"
}
```

### CPU Usage (`CPU_URL`)
```json
{
  "cpu": [0.0, 33.2, 0.0, 11.8, 0.0, 0.0, 0.0, 0.0, 0.2, 0.0, 13.2, 0.0, 0.0, 9.1, 50.1, 10.2, 2.1]
}
```

### CPU Temperature (`CPU_TEMP_URL`)
```json
{
  "cpu_temp": [45.0, 46.2, 45.8, 47.1]
}
```

## Manual Execution

```bash
# Run once
./display.sh

# Or with virtualenv
source ~/.virtualenvs/pimoroni/bin/activate
python nas.py
```

## Troubleshooting

### Display not updating
- Check that the cron job is running: `grep CRON /var/log/syslog`
- Verify API endpoints are accessible: `curl http://nas.local:5001`
- Check virtualenv Python path: `which python` (while activated)

### Font errors
- Ensure `FONT_DIR` points to the correct font directory
- Verify fonts exist: `ls -la /home/nas/fonts/`

### API errors
- Check network connectivity to NAS
- Verify API services are running on the NAS
- Review script output for error messages

## License

MIT
