"""Stable offline screen."""
from datetime import datetime
from PIL import Image, ImageDraw
from .common import RED, font, theme

class OfflineRenderer:
    name = "offline"
    def render(self, snapshot: dict, policy: dict, size: tuple[int, int]) -> Image.Image:
        colors = theme(policy.get("theme", "light"))
        image = Image.new("P", size, colors["background"]); draw = ImageDraw.Draw(image)
        draw.text((10, 12), "NAS OFFLINE", font=font(25, True), fill=RED)
        draw.text((10, 52), "Unable to reach monitoring service", font=font(12), fill=colors["foreground"])
        last = snapshot.get("last_success")
        if last:
            stamp = datetime.fromtimestamp(last).strftime("%Y-%m-%d %H:%M")
            draw.text((10, 76), f"Last update: {stamp}", font=font(11), fill=colors["foreground"])
        return image
