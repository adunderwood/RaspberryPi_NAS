#!/usr/bin/env python3
"""
Unified NAS Monitoring Service

Collects and serves system metrics via Flask API:
- CPU usage (%)
- CPU temperature (°C)
- Ambient temperature (°F/°C) from DS18B20 sensor
- RAID disk usage

Features:
- Automatic log rotation (configurable max lines)
- Robust error handling for corrupted sensor data
- Persistent storage that survives reboots
- Single service replaces 7+ separate scripts
"""

import os
import sys
import json
import time
import subprocess
import threading
from collections import deque
from datetime import datetime

import psutil
from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# Configuration
LOG_DIR = os.environ.get("LOG_DIR", "/home/nas/services")
MAX_LOG_LINES = int(os.environ.get("MAX_LOG_LINES", "2000"))  # Keep last 2000 readings
LOG_INTERVAL = int(os.environ.get("LOG_INTERVAL", "3"))  # Log every 3 seconds
SAVE_INTERVAL = int(os.environ.get("SAVE_INTERVAL", "60"))  # Save to disk every 60 seconds
TEMP_UNIT = os.environ.get("TEMP_UNIT", "F").upper()  # F or C for ambient temp

# Flask app setup
app = Flask(__name__)
CORS(app)

# In-memory circular buffers (auto-rotate when full)
cpu_usage_buffer = deque(maxlen=MAX_LOG_LINES)
cpu_temp_buffer = deque(maxlen=MAX_LOG_LINES)
ambient_temp_buffer = deque(maxlen=MAX_LOG_LINES)

# Thread-safe locks
cpu_lock = threading.Lock()
cpu_temp_lock = threading.Lock()
ambient_lock = threading.Lock()


# ============================================================================
# Utility Functions
# ============================================================================

def safe_float(value, default=-1.0):
    """Safely convert to float, return default on error."""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def load_log_file(filepath, buffer, lock):
    """Load existing log file into buffer, skipping corrupted lines."""
    if not os.path.exists(filepath):
        return

    try:
        with open(filepath, 'r') as f:
            lines = f.readlines()

        with lock:
            for line in lines[-MAX_LOG_LINES:]:  # Only load last N lines
                value = safe_float(line.strip())
                if value != -1.0:  # Only add valid values
                    buffer.append(value)

        print(f"Loaded {len(buffer)} entries from {filepath}")
    except Exception as e:
        print(f"Error loading {filepath}: {e}")


def save_log_file(filepath, buffer, lock):
    """Save buffer to file, keeping only last N lines."""
    try:
        with lock:
            data = list(buffer)  # Copy buffer safely

        with open(filepath, 'w') as f:
            for value in data:
                f.write(f"{value}\n")

        print(f"Saved {len(data)} entries to {filepath}")
    except Exception as e:
        print(f"Error saving {filepath}: {e}")


# ============================================================================
# Data Collection Functions
# ============================================================================

def get_cpu_usage():
    """Get current CPU usage percentage."""
    try:
        return psutil.cpu_percent(interval=1)
    except Exception as e:
        print(f"Error reading CPU usage: {e}")
        return -1.0


def get_cpu_temperature():
    """Read CPU temperature from thermal zone."""
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read().strip()
            return int(temp_str) / 1000.0  # Convert millidegrees to Celsius
    except Exception as e:
        print(f"Error reading CPU temperature: {e}")
        return -1.0


def find_ds18b20_sensor():
    """Find DS18B20 temperature sensor device ID."""
    try:
        devices = os.listdir('/sys/bus/w1/devices')
        for device in devices:
            if device != 'w1_bus_master1':
                return device
        return None
    except Exception as e:
        print(f"Error finding DS18B20 sensor: {e}")
        return None


def read_ds18b20_temperature(sensor_id):
    """Read temperature from DS18B20 sensor."""
    if not sensor_id:
        return -1.0, -1.0

    try:
        location = f'/sys/bus/w1/devices/{sensor_id}/w1_slave'
        with open(location) as f:
            text = f.read()

        secondline = text.split("\n")[1]
        temperaturedata = secondline.split(" ")[9]
        temperature = float(temperaturedata[2:])
        celsius = temperature / 1000
        fahrenheit = (celsius * 1.8) + 32
        return celsius, fahrenheit
    except Exception as e:
        print(f"Error reading DS18B20 temperature: {e}")
        return -1.0, -1.0


def get_raid_info():
    """Get RAID disk usage from df command."""
    try:
        df_output = subprocess.check_output(["df", "-h"], timeout=5).decode("utf-8")

        for line in df_output.splitlines():
            if "/dev/md" in line:
                parts = line.split()
                return {
                    "device": parts[0],
                    "total": parts[1],
                    "used": parts[2],
                    "free": parts[3],
                    "percent": parts[4],
                    "mount": parts[5]
                }

        return {"error": "No RAID arrays found"}
    except subprocess.TimeoutExpired:
        return {"error": "Command timeout"}
    except Exception as e:
        return {"error": str(e)}


# ============================================================================
# Logger Threads
# ============================================================================

def cpu_usage_logger():
    """Background thread: Log CPU usage."""
    log_file = os.path.join(LOG_DIR, "cpu_usage.log")

    # Load existing data
    load_log_file(log_file, cpu_usage_buffer, cpu_lock)

    last_save = time.time()

    while True:
        try:
            cpu_percent = get_cpu_usage()

            if cpu_percent != -1.0:
                with cpu_lock:
                    cpu_usage_buffer.append(cpu_percent)

            # Periodic save to disk
            if time.time() - last_save >= SAVE_INTERVAL:
                save_log_file(log_file, cpu_usage_buffer, cpu_lock)
                last_save = time.time()

            time.sleep(LOG_INTERVAL)
        except Exception as e:
            print(f"CPU usage logger error: {e}")
            time.sleep(LOG_INTERVAL)


def cpu_temp_logger():
    """Background thread: Log CPU temperature."""
    log_file = os.path.join(LOG_DIR, "cpu_temp.log")

    # Load existing data
    load_log_file(log_file, cpu_temp_buffer, cpu_temp_lock)

    last_save = time.time()

    while True:
        try:
            temp_c = get_cpu_temperature()

            if temp_c != -1.0:
                with cpu_temp_lock:
                    cpu_temp_buffer.append(temp_c)

            # Periodic save to disk
            if time.time() - last_save >= SAVE_INTERVAL:
                save_log_file(log_file, cpu_temp_buffer, cpu_temp_lock)
                last_save = time.time()

            time.sleep(LOG_INTERVAL)
        except Exception as e:
            print(f"CPU temp logger error: {e}")
            time.sleep(LOG_INTERVAL)


def ambient_temp_logger():
    """Background thread: Log ambient temperature from DS18B20."""
    log_file = os.path.join(LOG_DIR, "temperature.log")

    # Find sensor
    sensor_id = find_ds18b20_sensor()
    if not sensor_id:
        print("WARNING: DS18B20 sensor not found, ambient temperature logging disabled")
        return

    print(f"Found DS18B20 sensor: {sensor_id}")

    last_save = time.time()

    while True:
        try:
            celsius, fahrenheit = read_ds18b20_temperature(sensor_id)

            # Store based on configured unit
            if TEMP_UNIT == "C":
                temp_value = celsius
                temp_str = f"{celsius:.0f} C"
            else:
                temp_value = fahrenheit
                temp_str = f"{fahrenheit:.0f} F"

            if temp_value != -1.0:
                with ambient_lock:
                    # Store as string with unit (compatibility with old format)
                    ambient_temp_buffer.append(temp_str)

            # Periodic save to disk
            if time.time() - last_save >= SAVE_INTERVAL:
                # Save raw values to file
                try:
                    with ambient_lock:
                        data = list(ambient_temp_buffer)

                    with open(log_file, 'w') as f:
                        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        for value in data:
                            f.write(f"{timestamp} - INFO - {value}\n")

                    print(f"Saved {len(data)} temperature entries")
                except Exception as e:
                    print(f"Error saving temperature log: {e}")

                last_save = time.time()

            time.sleep(LOG_INTERVAL)
        except Exception as e:
            print(f"Ambient temp logger error: {e}")
            time.sleep(LOG_INTERVAL)


# ============================================================================
# Flask Routes
# ============================================================================

@app.route("/")
def index():
    """API information."""
    return jsonify({
        "service": "NAS Monitoring Service",
        "endpoints": {
            "/cpu": "CPU usage (last 18 readings)",
            "/cpu_temp": "CPU temperature (last 18 readings)",
            "/temperature": "Ambient temperature (latest)",
            "/raid": "RAID disk usage"
        }
    })


@app.route("/cpu")
def get_cpu():
    """Serve last 18 CPU usage readings."""
    with cpu_lock:
        data = list(cpu_usage_buffer)[-18:]  # Last 18 readings

    return jsonify({"cpu": data})


@app.route("/cpu_temp")
def get_cpu_temp():
    """Serve last 18 CPU temperature readings."""
    with cpu_temp_lock:
        data = list(cpu_temp_buffer)[-18:]  # Last 18 readings

    return jsonify({"cpu_temp": data})


@app.route("/temperature")
def get_temperature():
    """Serve latest ambient temperature."""
    with ambient_lock:
        if ambient_temp_buffer:
            latest = ambient_temp_buffer[-1]
        else:
            latest = "ERROR"

    return jsonify({"temperature": latest})


@app.route("/raid")
def get_raid():
    """Serve RAID disk usage."""
    return jsonify(get_raid_info())


# ============================================================================
# Main
# ============================================================================

def start_loggers():
    """Start all logging threads as daemons."""
    threads = [
        threading.Thread(target=cpu_usage_logger, daemon=True, name="CPU-Logger"),
        threading.Thread(target=cpu_temp_logger, daemon=True, name="CPUTemp-Logger"),
        threading.Thread(target=ambient_temp_logger, daemon=True, name="AmbientTemp-Logger"),
    ]

    for thread in threads:
        thread.start()
        print(f"Started {thread.name}")


if __name__ == '__main__':
    print("=" * 60)
    print("NAS Monitoring Service Starting")
    print("=" * 60)
    print(f"Log directory: {LOG_DIR}")
    print(f"Max log lines: {MAX_LOG_LINES}")
    print(f"Log interval: {LOG_INTERVAL}s")
    print(f"Save interval: {SAVE_INTERVAL}s")
    print(f"Temperature unit: {TEMP_UNIT}")
    print("=" * 60)

    # Ensure log directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Start background loggers
    start_loggers()

    # Give loggers time to initialize
    time.sleep(2)

    # Start Flask app
    try:
        # Use different ports based on endpoint in production
        # For now, we'll use port 5000 as the unified endpoint
        app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
