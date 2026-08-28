"""Default NAS overview screen."""
from PIL import Image, ImageDraw
from .common import BLACK, RED, bytes_short, font, temperature, theme

class OverviewRenderer:
    name = "overview"
    def render(self, snapshot: dict, policy: dict, size: tuple[int, int]) -> Image.Image:
        arrays = snapshot.get("storage", {}).get("arrays", [])
        array = arrays[0] if arrays else {}
        percent = float(array.get("usage_percent", 0))
        thresholds = policy.get("thresholds", {})
        alert = percent >= float(thresholds.get("storage_percent", 90))
        colors = theme("alert" if alert else policy.get("theme", "light"))
        image = Image.new("P", size, colors["background"]); draw = ImageDraw.Draw(image)
        width, height = size; compact = height <= 104
        large = font(43 if compact else 50, True); normal = font(12 if compact else 14, True)
        small = font(10 if compact else 12)
        draw.text((6, 1), f"{percent:.0f}%", font=large, fill=colors["foreground"])
        right = width // 2 + 8
        draw.text((right, 7), f"Total {bytes_short(array.get('bytes_total', 0))}", font=normal, fill=colors["foreground"])
        draw.text((right, 27), f"Used  {bytes_short(array.get('bytes_used', 0))}", font=normal, fill=colors["foreground"])
        draw.text((right, 47), f"Free  {bytes_short(array.get('bytes_free', 0))}", font=normal, fill=colors["foreground"])
        unit = policy.get("temperature_unit", "F")
        cpu_temp = temperature(snapshot.get("cpu", {}).get("temperature_c"), unit)
        ambient = temperature(snapshot.get("ambient", {}).get("temperature_c"), unit)
        draw.text((7, 62 if compact else 70), f"CPU {cpu_temp}  CASE {ambient}", font=normal, fill=colors["foreground"])
        history = snapshot.get("cpu", {}).get("usage_history", [])[-18:]
        if history:
            chart_x, chart_y, chart_w, chart_h = 33, height - 24, width - 40, 18
            draw.text((6, chart_y + 2), "CPU", font=small, fill=colors["foreground"])
            bar_w = max(1, chart_w // len(history))
            for index, point in enumerate(history):
                value = max(0, min(100, float(point.get("value", 0))))
                bar_h = max(1, round(chart_h * value / 100))
                draw.rectangle((chart_x + index * bar_w, chart_y + chart_h - bar_h,
                                chart_x + (index + 1) * bar_w - 1, chart_y + chart_h), fill=colors["accent"])
        return image
