# NAS Monitoring Service (Raspberry Pi 5)

A unified monitoring service that collects and serves NAS system metrics via Flask API endpoints. This single service replaces 7+ separate scripts and services.

## Features

- **Unified Service**: One process replaces multiple separate logger/server pairs
- **Automatic Log Rotation**: Keeps only last N lines (configurable, default 2000)
- **Robust Error Handling**: Gracefully handles corrupted sensor data and missing files
- **Persistent Storage**: Logs survive reboots while maintaining efficient disk usage
- **Thread-Safe**: Background logging threads with proper synchronization
- **Multi-Endpoint API**: Serves CPU, temperature, and RAID data

## Metrics Collected

| Endpoint | Description | Data Points |
|----------|-------------|-------------|
| `/cpu` | CPU usage percentage | Last 18 readings |
| `/cpu_temp` | CPU temperature (°C) | Last 18 readings |
| `/temperature` | Ambient temperature from DS18B20 sensor | Latest reading |
| `/raid` | RAID disk usage from `df -h` | Real-time |

## Installation

### 1. Install Dependencies

```bash
pip3 install psutil flask flask-cors python-dotenv
```

### 2. Configure Environment

Copy the example configuration:
```bash
cp .env.example .env
```

Edit `.env` to customize settings:
```bash
# Log directory
LOG_DIR=/home/nas/services

# Max lines per log file (controls size)
MAX_LOG_LINES=2000

# Collection interval (seconds)
LOG_INTERVAL=3

# Save to disk interval (seconds)
SAVE_INTERVAL=60

# Temperature unit (F or C)
TEMP_UNIT=F
```

### 3. Install Systemd Service

```bash
# Copy service file
sudo cp services/nas_service.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable nas_service

# Start service
sudo systemctl start nas_service

# Check status
sudo systemctl status nas_service
```

## Migration from Old Services

### Stop Old Services

```bash
sudo systemctl stop cpu_logger cpu_server
sudo systemctl stop cpu_temp_logger cpu_temp_server
sudo systemctl stop therm_logger therm_server
sudo systemctl stop raid_server

sudo systemctl disable cpu_logger cpu_server
sudo systemctl disable cpu_temp_logger cpu_temp_server
sudo systemctl disable therm_logger therm_server
sudo systemctl disable raid_server
```

### Cleanup Old Files (Optional)

```bash
# Backup old logs
mkdir -p ~/backup/logs
mv ~/services/*.log ~/backup/logs/
mv ~/services/*.bak* ~/backup/logs/

# Archive old service files
mkdir -p ~/backup/old_services
mv ~/services/cpu_logger.py ~/backup/old_services/
mv ~/services/cpu_server.py ~/backup/old_services/
mv ~/services/cpu_temp_logger.py ~/backup/old_services/
mv ~/services/cpu_temp_server.py ~/backup/old_services/
mv ~/services/therm_logger.py ~/backup/old_services/
mv ~/services/therm_server.py ~/backup/old_services/
mv ~/therm/raid.py ~/backup/old_services/
```

## API Examples

### Get CPU Usage
```bash
curl http://nas.local:5000/cpu
```
Response:
```json
{
  "cpu": [12.5, 15.3, 10.2, ..., 18.7]
}
```

### Get CPU Temperature
```bash
curl http://nas.local:5000/cpu_temp
```
Response:
```json
{
  "cpu_temp": [45.2, 46.1, 45.8, ..., 47.3]
}
```

### Get Ambient Temperature
```bash
curl http://nas.local:5000/temperature
```
Response:
```json
{
  "temperature": "72 F"
}
```

### Get RAID Info
```bash
curl http://nas.local:5000/raid
```
Response:
```json
{
  "device": "/dev/md0",
  "total": "1.8T",
  "used": "900G",
  "free": "900G",
  "percent": "50%",
  "mount": "/mnt/raid"
}
```

## Log Management

### Log Files

The service maintains three log files:
- `cpu_usage.log` - CPU percentage readings
- `cpu_temp.log` - CPU temperature readings (°C)
- `temperature.log` - Ambient temperature readings

### Automatic Rotation

Logs are automatically rotated to keep only the last `MAX_LOG_LINES` entries. This prevents unlimited growth.

**Example size with default settings (2000 lines):**
- CPU logs: ~20-30 KB each
- Total: < 100 KB (vs 35+ MB in old system)

### Manual Cleanup

```bash
# Clear all logs (service will recreate them)
rm ~/services/*.log

# Restart service
sudo systemctl restart nas_service
```

## Monitoring

### View Logs
```bash
# Follow service logs
sudo journalctl -u nas_service -f

# View recent logs
sudo journalctl -u nas_service -n 100
```

### Check Service Status
```bash
sudo systemctl status nas_service
```

### Test Endpoints
```bash
# Test all endpoints
curl http://localhost:5000/
curl http://localhost:5000/cpu
curl http://localhost:5000/cpu_temp
curl http://localhost:5000/temperature
curl http://localhost:5000/raid
```

## Troubleshooting

### Service won't start
- Check logs: `sudo journalctl -u nas_service -n 50`
- Verify Python dependencies: `pip3 list | grep -E "psutil|flask"`
- Check file permissions: `ls -la /home/nas/services/`

### DS18B20 sensor not found
- The service will log a warning and continue without ambient temperature
- Check sensor connection: `ls /sys/bus/w1/devices/`
- Verify 1-Wire is enabled in `/boot/config.txt`

### RAID data not showing
- Verify RAID array exists: `df -h | grep /dev/md`
- Check `df` command works: `df -h`

### High memory usage
- Reduce `MAX_LOG_LINES` in `.env`
- Decrease `LOG_INTERVAL` to collect less frequently

### Logs growing too large
- Default `MAX_LOG_LINES=2000` keeps logs under 100KB total
- Lower the value if needed: `MAX_LOG_LINES=1000`

## Architecture

### Old System (7+ Scripts)
```
cpu_logger.py → cpu_usage.log → cpu_server.py (port 5002)
cpu_temp_logger.py → cpu_temp.log → cpu_temp_server.py (port 5003)
therm_logger.py → temperature.log → therm_server.py (port 5000)
raid.py (port 5001)
```

### New System (1 Script)
```
nas_service.py
├── Background Threads (loggers)
│   ├── CPU usage → circular buffer → periodic save
│   ├── CPU temp → circular buffer → periodic save
│   └── Ambient temp → circular buffer → periodic save
└── Flask App (port 5000)
    ├── /cpu
    ├── /cpu_temp
    ├── /temperature
    └── /raid
```

## Benefits

✅ **Simplified Management**: 1 service instead of 7+
✅ **Reduced Disk Usage**: 100KB vs 35+ MB of logs
✅ **Better Reliability**: Robust error handling
✅ **Easier Debugging**: Centralized logging
✅ **Lower Memory**: Single Python process
✅ **Faster Response**: In-memory data access

## Development

### Run in Debug Mode
```bash
# Test locally
python3 nas_service.py
```

### Run with Custom Config
```bash
export MAX_LOG_LINES=500
export LOG_INTERVAL=5
python3 nas_service.py
```

## License

MIT
