"""Temperature-focused screen."""
from PIL import Image, ImageDraw
from .common import font, temperature, theme

class ThermalRenderer:
    name = "thermal"
    def render(self, snapshot: dict, policy: dict, size: tuple[int, int]) -> Image.Image:
        cpu = snapshot.get("cpu", {}).get("temperature_c"); ambient = snapshot.get("ambient", {}).get("temperature_c")
        thresholds = policy.get("thresholds", {})
        alert = ((cpu is not None and cpu >= float(thresholds.get("cpu_temperature_c", 80))) or
                 (ambient is not None and ambient >= float(thresholds.get("ambient_temperature_c", 35))))
        colors = theme("alert" if alert else policy.get("theme", "light")); unit = policy.get("temperature_unit", "F")
        image = Image.new("P", size, colors["background"]); draw = ImageDraw.Draw(image)
        width, height = size; value_font = font(31 if height <= 104 else 39, True); label_font = font(12, True)
        draw.text((8, 5), "THERMAL", font=font(13, True), fill=colors["accent"])
        draw.text((8, 29), temperature(cpu, unit), font=value_font, fill=colors["foreground"])
        draw.text((width//2+5, 29), temperature(ambient, unit), font=value_font, fill=colors["foreground"])
        draw.text((8, height-23), "CPU", font=label_font, fill=colors["foreground"])
        draw.text((width//2+5, height-23), "CASE", font=label_font, fill=colors["foreground"])
        draw.line((width//2, 24, width//2, height-8), fill=colors["accent"], width=2)
        return image
