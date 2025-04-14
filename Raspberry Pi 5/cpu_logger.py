import psutil
import time
import datetime

def log_cpu_usage(log_file="/home/nas/services/cpu_usage.log", interval=3):
    """
    Logs CPU usage to a file at specified intervals.

    Args:
        log_file (str, optional): Path to the log file. Defaults to "cpu_usage.log".
        interval (int, optional): Time interval in seconds between logs. Defaults to 1.
    """
    while True:
        with open(log_file, "a") as f:
            cpu_percent = psutil.cpu_percent(interval=interval)
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            #log_entry = f"{timestamp} - CPU Usage: {cpu_percent}%\n"
            log_entry = f"{cpu_percent}\n"
            f.write(log_entry)
            time.sleep(interval)

if __name__ == "__main__":
    log_cpu_usage()  # Starts logging CPU usage every second to cpu_usage.log
