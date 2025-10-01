import os
import requests
import json

from sparklines import sparklines

from inky import InkyPHAT
from inky.auto import auto

from PIL import Image, ImageFont, ImageDraw
from font_fredoka_one import FredokaOne

from dotenv import load_dotenv
load_dotenv()

# Setup
inky_display = auto()

# Load Environment Variables

MESSAGE = os.environ.get("MESSAGE", "Bunny NAS")

WARN_PERCENT = float(os.environ.get("WARN_PERCENT", "90"))
WARN_TEMP = float(os.environ.get("WARN_TEMP", "90"))

THEME = os.environ.get("THEME", "light")
THEME = THEME.lower()

NAS_URL = os.environ.get("NAS_URL")
TEMPERATURE_URL = os.environ.get("TEMPERATURE_URL")
CPU_URL = os.environ.get("CPU_URL")
CPU_TEMP_URL = os.environ.get("CPU_TEMP_URL")

FONT_DIR = os.environ.get("FONT_DIR", "/home/nas/fonts")

# Fonts
roboto_black = os.path.join(FONT_DIR, "roboto/Roboto-Black.ttf")
roboto_black_ttf = ImageFont.truetype(roboto_black, 56)

roboto_bold = os.path.join(FONT_DIR, "roboto/Roboto-ExtraBold.ttf")
roboto_bold_ttf = ImageFont.truetype(roboto_bold, 16)

roboto_med = os.path.join(FONT_DIR, "roboto/Roboto-Medium.ttf")
roboto_med_ttf = ImageFont.truetype(roboto_med, 16)

roboto_small = os.path.join(FONT_DIR, "roboto/Roboto-ExtraBold.ttf")
roboto_small_ttf = ImageFont.truetype(roboto_small, 14)

roboto_bold_right = os.path.join(FONT_DIR, "roboto/Roboto-ExtraBold.ttf")
roboto_bold_right_ttf = ImageFont.truetype(roboto_bold_right, 17)

roboto_med_right = os.path.join(FONT_DIR, "roboto/Roboto-Medium.ttf")
roboto_med_right_ttf = ImageFont.truetype(roboto_med, 17)

noto = os.path.join(FONT_DIR, "noto/NotoEmoji-Medium.ttf")
noto_ttf = ImageFont.truetype(noto, 16)
temperature_icon = u"\U0001F321"

sf_mono = os.path.join(FONT_DIR, "sf_mono/SFMonoRegular.otf")
sf_mono_ttf = ImageFont.truetype(sf_mono, 16)

def fetch_json(url):
    """Helper function to fetch JSON from a URL with error handling."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError:
        print("Invalid JSON response")
        return None

def getCPUInfo(url=CPU_URL):
    cpu_data = []
    data = fetch_json(url)
    if data:
        cpu_data = data.get("cpu", [])
    return cpu_data

# NAS Info
def getDiskInfo(url=NAS_URL):
    total = -1
    free = -1
    used = -1
    percent = "-1"

    data = fetch_json(url)
    if data:
        total = data.get("total", -1)
        used = data.get("used", -1)
        free = data.get("free", -1)
        percent = data.get("percent", "-1")

    return {
        "total": total,
        "used": used,
        "free": free,
        "percent": percent
    }

# Get Temperature

def cpuThermInfo(url=CPU_TEMP_URL):
    celsius = "-1"
    fahrenheit = "-1"

    data = fetch_json(url)
    if data and "cpu_temp" in data:
        temperature = data["cpu_temp"]

        # average all data points
        total = sum(int(round(i, 0)) for i in temperature)
        average_temp = total / len(temperature)

        # temperature comes in degrees C
        temp_C = average_temp
        temp_F = int(round((average_temp * 9/5) + 32, 0))

        degree_sign = u'\N{DEGREE SIGN}'

        celsius = str(temp_C) + degree_sign + " C"
        fahrenheit = str(temp_F) + degree_sign + " F"

    return {
        "celsius": celsius,
        "fahrenheit": fahrenheit
    }

def thermInfo(url=TEMPERATURE_URL):
    temperature = "-1"
    therm_alarm = False

    data = fetch_json(url)
    if data and "temperature" in data:
        temperature = data["temperature"]
        temp_int = temperature.replace(" F", "").replace(" C", "")
        temp_int = float(temp_int)

        degree_sign = u'\N{DEGREE SIGN}'

        temperature = temperature.replace(" F", degree_sign + " F")
        temperature = temperature.replace(" C", degree_sign + " C")

        # temperature
        if temp_int >= WARN_TEMP:
            therm_alarm = True

    return {
        "temperature": temperature,
        "therm_alarm": therm_alarm
    }

def getTheme(which=THEME):
    # Theme Colors
    which = which.lower()

    if which == "light":
        foreground_color = inky_display.BLACK
        background_color = inky_display.WHITE
        accent_color = inky_display.RED
    elif which == "dark":
        foreground_color = inky_display.WHITE
        background_color = inky_display.BLACK
        accent_color = inky_display.RED
    elif which == "red":
        foreground_color = inky_display.WHITE
        background_color = inky_display.RED
        accent_color = inky_display.WHITE
    else:
        # Default to light theme
        foreground_color = inky_display.BLACK
        background_color = inky_display.WHITE
        accent_color = inky_display.RED

    ret = {
        "foreground": foreground_color,
        "background": background_color,
        "accent": accent_color
    }

    return ret

def render(disk_info, therm_info, cpu_therm_info):
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
    percent_calc = int(percent.replace("%", ""))

    # adjustments
    if percent_calc < 20:
        left_offset = -10

    # disk use
    if percent_calc >= WARN_PERCENT:
        theme = getTheme("red")
        percent_color = theme["accent"]

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
    #draw.text((left_x, top_y + 62), "% Full", theme["foreground"], roboto_med_ttf)

    # Draw CPU Temperature
    cpu_temperature = cpu_therm_info["fahrenheit"]
    draw.text((left_x, top_y + 60), cpu_temperature, theme["foreground"], roboto_bold_ttf)

    # Draw Temperature
    therm_color = theme["foreground"]
    if therm_info["therm_alarm"]:
        therm_color = theme["accent"] # change color for alarm

    if therm_info["temperature"]:
        therm_temperature = therm_info["temperature"]
    else:
        therm_temperature = "-1"

    draw.text((left_x + 50, top_y + 60), temperature_icon, therm_color, noto_ttf)
    draw.text((left_x + 66, top_y + 60), therm_temperature, therm_color, roboto_bold_ttf)

    # Right Column

    right_x = image_width // 2 + column_spacing // 2
    right_x = right_x + 5

    text_rightA = "Total: \nUsed: \nFree: "
    text_rightB = disk_info["total"] + "\n" + disk_info["used"] + "\n" + disk_info["free"]

    draw.multiline_text((right_x, top_y + 8), text_rightA, font=roboto_med_right_ttf, fill=theme["foreground"], spacing=line_height)
    draw.multiline_text((right_x + 50, top_y + 8), text_rightB, font=roboto_bold_right_ttf, fill=theme["foreground"], spacing=line_height)

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
    cpu_therm_info = cpuThermInfo()

    render(disk_info, therm_info, cpu_therm_info)
