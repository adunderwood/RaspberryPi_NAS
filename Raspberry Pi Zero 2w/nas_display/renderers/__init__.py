"""Screen renderer registry."""
from .offline import OfflineRenderer
from .overview import OverviewRenderer
from .storage import StorageRenderer
from .thermal import ThermalRenderer

RENDERERS = {"overview": OverviewRenderer(), "storage": StorageRenderer(),
             "thermal": ThermalRenderer(), "offline": OfflineRenderer()}

def get_renderer(name: str):
    return RENDERERS.get(name, RENDERERS["overview"])
