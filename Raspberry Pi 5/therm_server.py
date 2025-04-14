import json
import os

from flask import Flask
from flask_cors import CORS

from dotenv import load_dotenv
load_dotenv()

import random

app = Flask(__name__)
CORS(app)

@app.route("/")
def temperature():
    # Example usage
    log_file = './temperature.log'
    last_value = get_last_log_value(log_file)
    temperature = "ERROR"

    if last_value:
        arr_last = last_value.split(" - ")
        temperature = arr_last[2]
        #print(f"The last value from the log file is: {last_value}")
        #print(temperature)

    #temperature = random.random()

    temperature_data = {"temperature": temperature}
    json_data = json.dumps(temperature_data)

    #json_data = json.dumps(temperature_data)
    return json_data


def get_last_log_value(log_filepath):
  try:
    with open(log_filepath, 'r') as file:
      lines = file.readlines()
      #print(lines[-1].strip())
      return lines[-1].strip()
  except FileNotFoundError:
    print(f"Error: File not found: {log_filepath}")
    return None
  except Exception as e:
    print(f"An error occurred: {e}")
    return None

def kill():
    quit()

if __name__ == '__main__':
    try:

      app.run(host='0.0.0.0', debug=True)
      #app.run(debug=True)

    except KeyboardInterrupt:
      kill()
