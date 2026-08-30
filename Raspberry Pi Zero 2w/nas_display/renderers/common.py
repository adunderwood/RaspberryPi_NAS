"""Shared three-colour eInk rendering helpers."""
from PIL import ImageFont

WHITE, BLACK, RED = 0, 1, 2

def font(size: int, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try: return ImageFont.truetype(name, size)
    except OSError: return ImageFont.load_default()

def theme(name: str):
    if name == "dark": return {"background": BLACK, "foreground": WHITE, "accent": WHITE}
    if name == "alert": return {"background": RED, "foreground": WHITE, "accent": WHITE}
    return {"background": WHITE, "foreground": BLACK, "accent": BLACK}

def temperature(value, unit: str) -> str:
    if value is None: return "--"
    if unit == "F": value = value * 9 / 5 + 32
    return f"{value:.0f}°{unit}"

def bytes_short(value: int) -> str:
    for suffix in ("B", "KiB", "MiB", "GiB", "TiB"):
        if abs(value) < 1024 or suffix == "TiB": return f"{value:.1f}{suffix}" if suffix != "B" else f"{value}B"
        value /= 1024

def safe_area(size: tuple[int, int]) -> tuple[int, int, int, int]:
    """Return the original InkyPHAT content inset, scaled for supported panels."""
    width, height = size
    left = max(12, round(width * 15 / 250))
    top = max(4, round(height * 5 / 122))
    right = width - max(8, round(width * 10 / 250))
    bottom = height - max(7, round(height * 10 / 122))
    return left, top, right, bottom
