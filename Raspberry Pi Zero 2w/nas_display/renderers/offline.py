"""Stable offline screen."""
from datetime import datetime
from PIL import Image, ImageDraw
from .common import RED, font, safe_area, theme

class OfflineRenderer:
    name = "offline"
    def render(self, snapshot: dict, policy: dict, size: tuple[int, int]) -> Image.Image:
        colors = theme(policy.get("theme", "light"))
        image = Image.new("P", size, colors["background"]); draw = ImageDraw.Draw(image)
        left, top, _, _ = safe_area(size)
        draw.text((left, top + 7), "NAS OFFLINE", font=font(25, True), fill=RED)
        draw.text((left, top + 47), "Unable to reach monitoring service", font=font(12), fill=colors["foreground"])
        last = snapshot.get("last_success")
        if last:
            stamp = datetime.fromtimestamp(last).strftime("%Y-%m-%d %H:%M")
            draw.text((left, top + 71), f"Last update: {stamp}", font=font(11), fill=colors["foreground"])
        return image
