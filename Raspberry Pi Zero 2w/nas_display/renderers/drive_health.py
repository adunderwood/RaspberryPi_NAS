"""Four-column physical drive health screen."""
from PIL import Image, ImageDraw
from .common import font, safe_area, temperature, theme

class DriveHealthRenderer:
    name = "drive_health"

    def render(self, snapshot: dict, policy: dict, size: tuple[int, int]) -> Image.Image:
        array = (snapshot.get("storage", {}).get("arrays") or [{}])[0]
        drives = sorted(array.get("drives") or [], key=lambda drive: drive.get("device", ""))[:4]
        degraded = int(array.get("degraded_drives", 0) or 0)
        alert = degraded > 0 or (bool(drives) and len(drives) < 4) or any(not drive.get("healthy", False) for drive in drives)
        colors = theme("alert" if alert else policy.get("theme", "light"))
        image = Image.new("P", size, colors["background"]); draw = ImageDraw.Draw(image)
        width, height = size; left, top, safe_right, safe_bottom = safe_area(size); compact = height <= 104
        draw.text((left, top), "DRIVE HEALTH", font=font(13, True), fill=colors["accent"])
        status = "UNKNOWN" if not drives else ("DEGRADED" if alert else "ALL HEALTHY")
        draw.text((safe_right, top + 1), status, anchor="ra", font=font(10, True), fill=colors["foreground"])
        column_width = (safe_right - left) / 4
        unit = policy.get("temperature_unit", "F")
        for index, label in enumerate("ABCD"):
            drive = drives[index] if index < len(drives) else None
            start = round(left + index * column_width); end = round(left + (index + 1) * column_width)
            center = (start + end) // 2
            if index:
                draw.line((start, top + 20, start, safe_bottom), fill=colors["accent"])
            draw.text((center, top + 18), label, anchor="ma", font=font(18 if compact else 21, True), fill=colors["foreground"])
            icon_y = top + (43 if compact else 48); radius = 7
            draw.ellipse((center-radius, icon_y-radius, center+radius, icon_y+radius), outline=colors["foreground"], width=2)
            healthy = bool(drive and drive.get("healthy", False))
            if healthy:
                draw.line((center-4, icon_y, center-1, icon_y+4), fill=colors["foreground"], width=2)
                draw.line((center-1, icon_y+4, center+5, icon_y-4), fill=colors["foreground"], width=2)
            elif drive:
                draw.line((center-4, icon_y-4, center+4, icon_y+4), fill=colors["foreground"], width=2)
                draw.line((center+4, icon_y-4, center-4, icon_y+4), fill=colors["foreground"], width=2)
            else:
                draw.line((center-4, icon_y, center+4, icon_y), fill=colors["foreground"], width=2)
            state = "OK" if healthy else ("FAULT" if drive else "MISSING")
            draw.text((center, icon_y + 11), state, anchor="ma", font=font(8 if compact else 9, True), fill=colors["foreground"])
            value = drive.get("temperature_c") if drive else None
            draw.text((center, safe_bottom - (12 if compact else 13)), temperature(value, unit), anchor="ma",
                      font=font(10 if compact else 12, True), fill=colors["foreground"])
        return image
