"""Screen renderer registry."""
from .offline import OfflineRenderer
from .overview import OverviewRenderer
from .storage import StorageRenderer
from .thermal import ThermalRenderer
from .drive_health import DriveHealthRenderer

RENDERERS = {"overview": OverviewRenderer(), "storage": StorageRenderer(),
             "thermal": ThermalRenderer(), "drive_health": DriveHealthRenderer(), "offline": OfflineRenderer()}

def get_renderer(name: str):
    return RENDERERS.get(name, RENDERERS["overview"])
