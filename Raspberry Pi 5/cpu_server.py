import numpy as np

import json
import os

from flask import Flask
from flask_cors import CORS

from dotenv import load_dotenv
load_dotenv()

import random

app = Flask(__name__)
CORS(app)

class NumpyEncoder(json.JSONEncoder):
    """ Special json encoder for numpy types """
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return json.JSONEncoder.default(self, obj)

@app.route("/")
def getCPULog(num_lines = 18):
    filename = "./cpu_usage.log"
    json_data = {}

    with open(filename, 'r') as file:
        lines = file.readlines()
        lines = np.array(lines)
        lines = lines.astype(float)
        json_data = {
            "cpu": lines[-num_lines:]
        }

    return json.dumps(json_data, cls=NumpyEncoder)

def kill():
    quit()

if __name__ == '__main__':
    try:

      app.run(host='0.0.0.0', port=5002, debug=True)
      #app.run(debug=True)

    except KeyboardInterrupt:
      kill()
