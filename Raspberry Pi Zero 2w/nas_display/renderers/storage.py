"""Storage-focused screen."""
from PIL import Image, ImageDraw
from .common import bytes_short, font, theme

class StorageRenderer:
    name = "storage"
    def render(self, snapshot: dict, policy: dict, size: tuple[int, int]) -> Image.Image:
        array = (snapshot.get("storage", {}).get("arrays") or [{}])[0]
        percent = float(array.get("usage_percent", 0)); thresholds = policy.get("thresholds", {})
        colors = theme("red" if percent >= float(thresholds.get("storage_percent", 90)) else policy.get("theme", "light"))
        image = Image.new("P", size, colors["background"]); draw = ImageDraw.Draw(image)
        width, height = size
        draw.text((8, 5), "STORAGE", font=font(13, True), fill=colors["accent"])
        draw.text((8, 23), f"{percent:.1f}%", font=font(42 if height <= 104 else 50, True), fill=colors["foreground"])
        right = width // 2 + 5; normal = font(13 if height > 104 else 11, True)
        draw.text((right, 22), f"Total  {bytes_short(array.get('bytes_total', 0))}", font=normal, fill=colors["foreground"])
        draw.text((right, 43), f"Used   {bytes_short(array.get('bytes_used', 0))}", font=normal, fill=colors["foreground"])
        draw.text((right, 64), f"Free   {bytes_short(array.get('bytes_free', 0))}", font=normal, fill=colors["foreground"])
        bar_y = height - 13; draw.rounded_rectangle((8, bar_y, width-8, height-6), radius=3, outline=colors["foreground"])
        fill_x = 9 + round((width-18) * min(100, percent) / 100)
        if fill_x > 9: draw.rectangle((9, bar_y+1, fill_x, height-7), fill=colors["accent"])
        return image
