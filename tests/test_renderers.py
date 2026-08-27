from nas_display.renderers.offline import OfflineRenderer
from nas_display.renderers.overview import OverviewRenderer
from nas_display.renderers.storage import StorageRenderer
from nas_display.renderers.thermal import ThermalRenderer
from nas_display.renderers.drive_health import DriveHealthRenderer

def test_renderers_produce_panel_sized_palette_images():
    snapshot = {"cpu":{"temperature_c":50,"usage_history":[{"value":10},{"value":50}]},
                "ambient":{"temperature_c":25}, "storage":{"arrays":[{"usage_percent":48.1,
                "bytes_total":5905452703744,"bytes_used":2841154748416,"bytes_free":3064281178112,
                "degraded_drives":0,"drives":[{"device":"/dev/sda","state":"in_sync","errors":0,"healthy":True}]}]}}
    policy = {"theme":"dark","temperature_unit":"F","thresholds":{"storage_percent":90}}
    for size in ((212, 104), (250, 122)):
        for renderer in (OverviewRenderer(), StorageRenderer(), ThermalRenderer(), DriveHealthRenderer()):
            image = renderer.render(snapshot, policy, size)
            assert image.size == size and image.mode == "P"
        offline = OfflineRenderer().render({"last_success":1000}, policy, size)
        assert offline.size == size and offline.mode == "P"
