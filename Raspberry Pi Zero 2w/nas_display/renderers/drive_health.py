"""Linux MD member-drive health screen."""
from pathlib import Path
from PIL import Image, ImageDraw
from .common import font, theme

class DriveHealthRenderer:
    name = "drive_health"

    def render(self, snapshot: dict, policy: dict, size: tuple[int, int]) -> Image.Image:
        array = (snapshot.get("storage", {}).get("arrays") or [{}])[0]
        drives = array.get("drives") or []
        degraded = int(array.get("degraded_drives", 0) or 0)
        alert = degraded > 0 or any(not drive.get("healthy", False) for drive in drives)
        colors = theme("alert" if alert else policy.get("theme", "light"))
        image = Image.new("P", size, colors["background"]); draw = ImageDraw.Draw(image)
        width, height = size
        draw.text((8, 5), "DRIVE HEALTH", font=font(13, True), fill=colors["accent"])
        status = "UNKNOWN" if not drives else ("DEGRADED" if alert else "ALL HEALTHY")
        draw.text((width - 8, 6), status, anchor="ra", font=font(11, True), fill=colors["foreground"])
        if not drives:
            draw.text((width // 2, height // 2 - 4), "NO MEMBER DATA", anchor="mm",
                      font=font(19, True), fill=colors["foreground"])
            draw.text((width // 2, height // 2 + 18), "Linux MD array not detected", anchor="mm",
                      font=font(10), fill=colors["foreground"])
            return image
        top = 29; row_height = max(18, (height - top - 4) // min(4, len(drives)))
        for index, drive in enumerate(drives[:4]):
            y = top + index * row_height
            name = Path(drive.get("device", "unknown")).name
            healthy = bool(drive.get("healthy", False))
            state = "OK" if healthy else str(drive.get("state", "FAULT")).replace("_", " ").upper()
            draw.text((10, y), name, font=font(14, True), fill=colors["foreground"])
            draw.text((width - 10, y), state, anchor="ra", font=font(13, True),
                      fill=colors["foreground"] if healthy else colors["accent"])
            if index < min(4, len(drives)) - 1:
                draw.line((8, y + row_height - 4, width - 8, y + row_height - 4), fill=colors["accent"])
        return image
