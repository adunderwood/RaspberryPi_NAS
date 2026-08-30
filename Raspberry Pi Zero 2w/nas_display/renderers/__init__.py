"""Screen renderer registry."""
from .offline import OfflineRenderer
from .overview import OverviewRenderer
from .storage import StorageRenderer
from .thermal import ThermalRenderer
from .drive_health import DriveHealthRenderer
from .cpu_memory import CpuMemoryRenderer

RENDERERS = {"overview": OverviewRenderer(), "storage": StorageRenderer(),
             "thermal": ThermalRenderer(), "drive_health": DriveHealthRenderer(),
             "cpu_memory": CpuMemoryRenderer(), "offline": OfflineRenderer()}

def get_renderer(name: str):
    return RENDERERS.get(name, RENDERERS["overview"])
