#!/usr/bin/env python
import os

import logging
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
import os

def setup_logger(log_file_path, max_file_size_bytes, backup_count, when='D'):
    """
    Sets up a logger that writes to a file, with rotation based on size and time.

    Args:
        log_file_path (str): Path to the log file.
        max_file_size_bytes (int): Maximum size of the log file in bytes before rotation.
        backup_count (int): Number of backup log files to keep.
        when (str, optional): Specifies the interval for rotating the log file, defaults to 'D' (daily).
                              Other options are 'H' (hourly), 'M' (minutes), 'W' (weekly), etc.
    """
    log_dir = os.path.dirname(log_file_path)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)  # Set the minimum logging level

    # Create a formatter
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    # Create handlers
    rotating_handler = RotatingFileHandler(log_file_path, maxBytes=max_file_size_bytes, backupCount=backup_count)
    rotating_handler.setFormatter(formatter)

    time_rotating_handler = TimedRotatingFileHandler(log_file_path, when=when, backupCount=backup_count)
    time_rotating_handler.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(rotating_handler)
    logger.addHandler(time_rotating_handler)

    return logger

def sensor():
    for i in os.listdir('/sys/bus/w1/devices'):
        if i != 'w1_bus_master1':
            ds18b20 = i
    return ds18b20

def read(ds18b20):
    location = '/sys/bus/w1/devices/' + ds18b20 + '/w1_slave'
    tfile = open(location)
    text = tfile.read()
    tfile.close()
    secondline = text.split("\n")[1]
    temperaturedata = secondline.split(" ")[9]
    temperature = float(temperaturedata[2:])
    celsius = temperature / 1000
    farenheit = (celsius * 1.8) + 32
    return celsius, farenheit

def loop(ds18b20, logger):
    log_unit = os.environ.get("LOG_UNIT", "F")

    while True:
        if read(ds18b20) != None:
            if (log_unit.upper() == "C"):
                print ("Current temperature : %0.1f F" % read(ds18b20)[0])
                logger.info("%0.0f C" % read(ds18b20)[0])
            else:
                print ("Current temperature : %0.1f F" % read(ds18b20)[1])
                logger.info("%0.0f F" % read(ds18b20)[1])

def kill():
    quit()

if __name__ == '__main__':
    try:
        serialNum = sensor()

        log_size = os.environ.get("LOG_SIZE", 1024) # default to 1gb max size
        log_days = os.environ.get("LOG_DAYS", 30) # default to 30 days

        log_file = 'temperature.log'
        max_size = 1024 * 1024 * log_size # 100MB
        backups = log_days

        logger = setup_logger(log_file, max_size, backups)

        # Example log messages
        #logger.debug('This is a debug message')
        #logger.info('This is an info message')
        #logger.warning('This is a warning message')
        #logger.error('This is an error message')
        #logger.critical('This is a critical message')
        
        loop(serialNum, logger)
    except KeyboardInterrupt:
        kill()
