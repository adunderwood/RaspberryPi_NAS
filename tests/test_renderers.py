from nas_display.renderers.offline import OfflineRenderer
from nas_display.renderers.overview import OverviewRenderer

def test_renderers_produce_panel_sized_palette_images():
    snapshot = {"cpu":{"temperature_c":50,"usage_history":[{"value":10},{"value":50}]},
                "ambient":{"temperature_c":25}, "storage":{"arrays":[{"usage_percent":48.1,
                "bytes_total":5905452703744,"bytes_used":2841154748416,"bytes_free":3064281178112}]}}
    policy = {"theme":"dark","temperature_unit":"F","thresholds":{"storage_percent":90}}
    for size in ((212, 104), (250, 122)):
        image = OverviewRenderer().render(snapshot, policy, size)
        assert image.size == size and image.mode == "P"
        offline = OfflineRenderer().render({"last_success":1000}, policy, size)
        assert offline.size == size and offline.mode == "P"
