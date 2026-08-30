"""CPU and memory utilization screen."""
from PIL import Image, ImageDraw
from .common import font, safe_area, theme

class CpuMemoryRenderer:
    name = "cpu_memory"

    def render(self, snapshot: dict, policy: dict, size: tuple[int, int]) -> Image.Image:
        colors = theme(policy.get("theme", "light"))
        image = Image.new("P", size, colors["background"]); draw = ImageDraw.Draw(image)
        width, height = size; left, top, safe_right, safe_bottom = safe_area(size)
        cpu = float(snapshot.get("cpu", {}).get("usage_percent") or 0)
        memory = float(snapshot.get("memory", {}).get("usage_percent") or 0)
        compact = height <= 104; value_font = font(32 if compact else 39, True)
        draw.text((left, top), "CPU & RAM", font=font(13, True), fill=colors["accent"])
        divider = width // 2
        columns = ((left, divider - 9, "CPU", cpu), (divider + 9, safe_right, "RAM", memory))
        for start, end, label, value in columns:
            draw.text((start, top + 21), label, font=font(12, True), fill=colors["foreground"])
            draw.text((start, top + 34), f"{value:.0f}%", font=value_font, fill=colors["foreground"])
            bar_y = safe_bottom - 8
            draw.rounded_rectangle((start, bar_y, end, safe_bottom), radius=3, outline=colors["foreground"])
            fill_end = start + 1 + round((end - start - 2) * min(100, max(0, value)) / 100)
            if fill_end > start + 1:
                draw.rectangle((start + 1, bar_y + 1, fill_end, safe_bottom - 1), fill=colors["foreground"])
        draw.line((divider, top + 20, divider, safe_bottom), fill=colors["accent"], width=2)
        return image
