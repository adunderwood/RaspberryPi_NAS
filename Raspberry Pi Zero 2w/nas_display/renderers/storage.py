"""Storage-focused screen."""
from PIL import Image, ImageDraw
from .common import bytes_short, font, safe_area, theme

class StorageRenderer:
    name = "storage"
    def render(self, snapshot: dict, policy: dict, size: tuple[int, int]) -> Image.Image:
        array = (snapshot.get("storage", {}).get("arrays") or [{}])[0]
        percent = float(array.get("usage_percent", 0)); thresholds = policy.get("thresholds", {})
        colors = theme("alert" if percent >= float(thresholds.get("storage_percent", 90)) else policy.get("theme", "light"))
        image = Image.new("P", size, colors["background"]); draw = ImageDraw.Draw(image)
        width, height = size; left, top, safe_right, safe_bottom = safe_area(size)
        draw.text((left, top), "STORAGE", font=font(13, True), fill=colors["accent"])
        draw.text((left, top + 18), f"{percent:.1f}%", font=font(42 if height <= 104 else 50, True), fill=colors["foreground"])
        right = width // 2 + 5; normal = font(13 if height > 104 else 11, True)
        draw.text((right, top + 17), f"Total  {bytes_short(array.get('bytes_total', 0))}", font=normal, fill=colors["foreground"])
        draw.text((right, top + 38), f"Used   {bytes_short(array.get('bytes_used', 0))}", font=normal, fill=colors["foreground"])
        draw.text((right, top + 59), f"Free   {bytes_short(array.get('bytes_free', 0))}", font=normal, fill=colors["foreground"])
        bar_y = safe_bottom - 7; draw.rounded_rectangle((left, bar_y, safe_right, safe_bottom), radius=3, outline=colors["foreground"])
        fill_x = left + 1 + round((safe_right-left-2) * min(100, percent) / 100)
        if fill_x > left + 1: draw.rectangle((left+1, bar_y+1, fill_x, safe_bottom-1), fill=colors["accent"])
        return image
