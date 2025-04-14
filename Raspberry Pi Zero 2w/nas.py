import numpy as np

import os
import requests
import json
import emoji

from sparklines import sparklines
from io import StringIO

from inky import InkyPHAT
from inky.auto import auto

from PIL import Image, ImageFont, ImageDraw
from font_fredoka_one import FredokaOne

from dotenv import load_dotenv
load_dotenv()

# Setup
inky_display = auto()

# Load Enviornment Variables

MESSAGE = os.environ.get("MESSAGE", "Bunny NAS")

WARN_PERCENT = float(os.environ.get("WARN_PERCENT", "90"))
WARN_TEMP = float(os.environ.get("WARN_TEMP", "90"))

THEME = os.environ.get("THEME", "light")
THEME = THEME.lower()

NAS_URL = os.environ.get("NAS_URL")
TEMPERATURE_URL = os.environ.get("TEMPERATURE_URL")
CPU_URL = os.environ.get("CPU_URL")

# Fonts
roboto_black = "/home/nas/fonts/roboto/Roboto-Black.ttf"  # Replace with the actual path to your font file
roboto_black_ttf = ImageFont.truetype(roboto_black, 56)

roboto_bold = "/home/nas/fonts/roboto/Roboto-ExtraBold.ttf"
roboto_bold_ttf = ImageFont.truetype(roboto_bold, 16)

roboto_med = "/home/nas/fonts/roboto/Roboto-Medium.ttf"  # Replace with the actual path to your font file
roboto_med_ttf = ImageFont.truetype(roboto_med, 16)

roboto_small = "/home/nas/fonts/roboto/Roboto-ExtraBold.ttf"  # Replace with the actual path to your font file
roboto_small_ttf = ImageFont.truetype(roboto_small, 14)

roboto_bold_right = "/home/nas/fonts/roboto/Roboto-ExtraBold.ttf"  # Replace with the actual path to your font file
roboto_bold_right_ttf = ImageFont.truetype(roboto_bold_right, 17)

roboto_med_right = "/home/nas/fonts/roboto/Roboto-Medium.ttf"  # Replace with the actual path to your font file
roboto_med_right_ttf = ImageFont.truetype(roboto_med, 17)

noto = "/home/nas/fonts/noto/NotoEmoji-Medium.ttf"
noto_ttf = ImageFont.truetype(noto, 16)
temperature_icon = u"\U0001F321"

sf_mono = "/home/nas/fonts/sf_mono/SFMonoRegular.otf"
sf_mono_ttf = ImageFont.truetype(sf_mono, 16)

def getCPUInfo(url = CPU_URL):
    cpu_data = []

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        cpu_data = data["cpu"]

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except json.JSONDecodeError:
        print("Invalid JSON response")

    return cpu_data

# NAS Info
def getDiskInfo(url = NAS_URL):
    #print(url)
    #response = requests.get(url)

    total = -1
    free = -1
    used = -1
    percent = -1

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()
        total = data["total"]
        used = data["used"]
        free = data["free"]
        percent = data["percent"]

        output = f"Total: {total}\nUsed: {used}\nFree: {free}\nPercent: {percent}"
        #print(output)

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except json.JSONDecodeError:
        print("Invalid JSON response")

    ret = {
        "total": total,
        "used": used,
        "free": free,
        "percent": percent
    }

    return ret

# Get Temperature

def thermInfo(url = TEMPERATURE_URL):
    #therm_url = "http://nas.local:5000"
    temperature = -1
    #response = requests.get(url)
    therm_alarm = False

    try:
        response = requests.get(url)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

        data = response.json()

        temperature = data["temperature"]
        temp_int = temperature.replace(" F","").replace(" C","")
        #print(temp_int)
        temp_int = float(temp_int)

        degree_sign = u'\N{DEGREE SIGN}'

        temperature = temperature.replace (" F", degree_sign + " F")
        temperature = temperature.replace (" C", degree_sign + " C")

        # temperature
        if (temp_int >= WARN_TEMP):
            therm_alarm = True
            #THEME = "red"
            
        #print("Temperature: " + temperature)

    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except json.JSONDecodeError:
        print("Invalid JSON response")

    ret = {
        "temperature": temperature,
        "therm_alarm": therm_alarm
    }

    return ret

def getTheme(which = THEME):
    # Theme Colors
    which = which.lower()

    if which == "light":
        foreground_color = inky_display.BLACK
        background_color = inky_display.WHITE
        accent_color = inky_display.RED

    if which == "dark":
        foreground_color = inky_display.WHITE
        background_color = inky_display.BLACK
        accent_color = inky_display.RED

    if which == "red":
        foreground_color = inky_display.WHITE
        background_color = inky_display.RED
        accent_color = inky_display.WHITE

    ret = {
        "foreground": foreground_color,
        "background": background_color,
        "accent": accent_color
    }

    return ret

def render(disk_info, therm_info):
    theme = getTheme()

    # Percent is a featured element and affected by changes below
    percent = disk_info["percent"]
    percent_color = theme["foreground"]

    # Layout defaults
    image_width = inky_display.width
    image_height = inky_display.height

    left_x = 20
    top_y = 5
    column_spacing = 15

    text_left = percent
    left_offset = 0
    line_height = 16 * .6

    # Warning, change theme
    percent_calc = int(percent.replace("%",""))
    #adjustments
    if (percent_calc < 20):
        left_offset = -10
        
    # disk use
    if (percent_calc >= WARN_PERCENT):
        percent_color = theme["accent"]
        THEME = "red"
        
    # Create a new image
    img = Image.new("P", (inky_display.width, inky_display.height), theme["background"])
    draw = ImageDraw.Draw(img)

    # Fonts
    font_large = ImageFont.truetype(FredokaOne, 48)
    font = ImageFont.truetype(FredokaOne, 16)

    # Left Column 

    # Draw Percent
    draw.multiline_text((left_x - 5, top_y), text_left, font=roboto_black_ttf, fill=percent_color)

    # Draw Percent Label
    draw.text((left_x, top_y + 62), "% Full", theme["foreground"], roboto_med_ttf)

    # Draw Temperature
    therm_color = theme["foreground"]
    if therm_info["therm_alarm"]:
        therm_color = theme["accent"] # change color for alarm

    draw.text((left_x + 46, top_y + 60), temperature_icon, therm_color, noto_ttf)
    draw.text((left_x + 62, top_y + 60), therm_info["temperature"], therm_color, roboto_bold_ttf)

    # Right Column
    
    right_x = image_width // 2 + column_spacing // 2
    right_x = right_x + 5

    text_rightA = "Total: \nUsed: \nFree: "
    text_rightB = disk_info["total"] + "\n" + disk_info["used"] + "\n" + disk_info["free"]

    draw.multiline_text((right_x, top_y + 8), text_rightA, font=roboto_med_right_ttf, fill=theme["foreground"], spacing=line_height)
    draw.multiline_text((right_x + 50, top_y + 8), text_rightB, font=roboto_bold_right_ttf, fill=theme["foreground"], spacing=line_height)

    #draw footer
    #rectangle_coords = (0, inky_display.height - 30, inky_display.width, inky_display.height)
    #draw.rectangle(rectangle_coords, outline=theme["foreground"], fill=theme["foreground"])

    #_, _, w, h = font.getbbox(MESSAGE)
    #center = (inky_display.width / 2) - (w / 2)

    #draw.text((center, inky_display.height - 26), MESSAGE, theme["background"], roboto_bold_right_ttf)

    #data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5, 10, 3, 1, 1, 4, 8] #17...
    #data = [0.0, 33.2, 0.0, 11.8, 0.0, 0.0, 0.0, 0.0, 0.2, 0.0, 13.2, 0.0, 0.0, 9.1, 50.1, 10.2, 2.1]
    data = getCPUInfo()
    sparkline = ''.join(sparklines(data))

    draw.multiline_text((left_x - 1, inky_display.height - 25), "CPU ", font=roboto_small_ttf, fill=theme["foreground"])
    draw.multiline_text((left_x + 31, inky_display.height - 31), sparkline, font=sf_mono_ttf, fill=theme["foreground"])

    # Set display border to black
    inky_display.set_border(inky_display.BLACK)
    inky_display.set_image(img)
    inky_display.show()

if __name__ == '__main__':
    disk_info = getDiskInfo()
    therm_info = thermInfo()

    render(disk_info, therm_info)
