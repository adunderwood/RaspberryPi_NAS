"""One-time startup logo rendered before the first monitoring request."""
from pathlib import Path
from PIL import Image
from .common import BLACK, WHITE

LOGO_PATH = Path(__file__).parents[1] / "assets" / "logo.png"
PALETTE = ((255, 255, 255, WHITE), (0, 0, 0, BLACK))

class StartupRenderer:
    name = "startup"

    def render(self, _snapshot: dict, _policy: dict, size: tuple[int, int]) -> Image.Image:
        source = Image.open(LOGO_PATH).convert("RGB")
        if source.size != size:
            source = source.resize(size, Image.Resampling.LANCZOS)
        image = Image.new("P", size, BLACK)
        raw = source.tobytes()
        pixels = zip(raw[0::3], raw[1::3], raw[2::3])
        image.putdata([
            min(PALETTE, key=lambda color: sum((pixel[channel] - color[channel]) ** 2
                                               for channel in range(3)))[3]
            for pixel in pixels
        ])
        return image
