"""Screen renderer registry."""
from .offline import OfflineRenderer
from .overview import OverviewRenderer

RENDERERS = {"overview": OverviewRenderer(), "offline": OfflineRenderer()}

def get_renderer(name: str):
    return RENDERERS.get(name, RENDERERS["overview"])
