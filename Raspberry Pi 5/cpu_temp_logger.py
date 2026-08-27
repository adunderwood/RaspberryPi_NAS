import psutil
import time
import datetime

def get_cpu_temperature():
    """Reads the CPU temperature from /sys/class/thermal/thermal_zone0/temp.

    Returns:
        float: The CPU temperature in degrees Celsius, or None if an error occurs.
    """
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read().strip()
            temp_celsius = int(temp_str) / 1000.0
            return temp_celsius
    except FileNotFoundError:
        print("Error: Temperature file not found.")
        return None
    except ValueError:
        print("Error: Invalid temperature value.")
        return None
    except Exception as e:
         print(f"An unexpected error occurred: {e}")
         return None

def log_cpu_temp(log_file="/home/nas/services/cpu_temp.log", interval=3):
    """
    Logs CPU usage to a file at specified intervals.

    Args:
        log_file (str, optional): Path to the log file. Defaults to "cpu_usage.log".
        interval (int, optional): Time interval in seconds between logs. Defaults to 1.
    """
    while True:
        with open(log_file, "a") as f:
            cpu_temp = get_cpu_temperature()
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            log_entry = f"{cpu_temp}\n"
            f.write(log_entry)
            time.sleep(interval)

if __name__ == "__main__":
    log_cpu_temp()  # Starts logging CPU usage every second to cpu_usage.log
