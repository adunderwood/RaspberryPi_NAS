"""Lazy hardware adapter for Pimoroni Inky displays."""
from PIL import Image

class InkyHardware:
    def __init__(self):
        from inky.auto import auto
        self.device = auto()

    @property
    def size(self) -> tuple[int, int]: return self.device.width, self.device.height

    def show(self, image: Image.Image) -> None:
        self.device.set_border(self.device.BLACK)
        self.device.set_image(image)
        self.device.show()
