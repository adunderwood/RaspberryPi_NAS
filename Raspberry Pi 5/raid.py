import json
import os
import subprocess
import re

from flask import Flask
from flask_cors import CORS

from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
CORS(app)

@app.route("/")
def get_raid_usage():
    try:
        df_output = subprocess.check_output(["df", "-h"]).decode("utf-8")
        
        raid_devices = []
        for line in df_output.splitlines():
            if "/dev/md" in line:
                raid_devices.append(line)
        
        if not raid_devices:
          return "No RAID arrays found."

        result = ""

        for device in raid_devices:
          parts = device.split()
          device_name = parts[0]
          total_size = parts[1]
          used_space = parts[2]
          available_space = parts[3]
          usage_percentage = parts[4]
          mount_point = parts[5]
          
          result += f"RAID Device: {device_name}\n"
          result += f"  Total Size: {total_size}\n"
          result += f"  Used Space: {used_space}\n"
          result += f"  Available Space: {available_space}\n"
          result += f"  Usage Percentage: {usage_percentage}\n"
          result += f"  Mount Point: {mount_point}\n\n"

          result_json = {
              "device": device_name,
              "total": total_size,
              "used": used_space,
              "free": available_space,
              "percent": usage_percentage,
              "mount": mount_point
          }

        #print(result_json)
        return result_json

    except subprocess.CalledProcessError as e:
        return f"Error executing command: {e}"
    except FileNotFoundError:
        return "Command 'df' not found."

def kill():
    quit()

if __name__ == '__main__':
    try:

      app.run(host='0.0.0.0', port=5001, debug=True)
      #app.run(debug=True)

    except KeyboardInterrupt:
      kill()


#if __name__ == "__main__":
#    raid_usage_info = get_raid_usage()
#    print(raid_usage_info)
