from nas_display.renderers.offline import OfflineRenderer
from nas_display.renderers.overview import OverviewRenderer
from nas_display.renderers.storage import StorageRenderer
from nas_display.renderers.thermal import ThermalRenderer
from nas_display.renderers.drive_health import DriveHealthRenderer
from nas_display.renderers.common import safe_area
from nas_display.renderers.startup import StartupRenderer

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

def test_renderers_preserve_original_panel_safe_area():
    snapshot = {"cpu":{"temperature_c":50,"usage_history":[{"value":25}]},
                "ambient":{"temperature_c":25}, "storage":{"arrays":[{"usage_percent":48.1,
                "bytes_total":5905452703744,"bytes_used":2841154748416,"bytes_free":3064281178112,
                "degraded_drives":0,"drives":[{"device":"/dev/sda","state":"in_sync","errors":0,"healthy":True}]}]}}
    policy = {"theme":"light","temperature_unit":"F","thresholds":{"storage_percent":90}}
    renderers = (OverviewRenderer(), StorageRenderer(), ThermalRenderer(), DriveHealthRenderer(), OfflineRenderer())
    for size in ((212, 104), (250, 122)):
        left, top, right, bottom = safe_area(size)
        for renderer in renderers:
            image = renderer.render(snapshot, policy, size); background = image.getpixel((0, 0))
            assert all(image.getpixel((x, y)) == background for x in range(left) for y in range(size[1]))
            assert all(image.getpixel((x, y)) == background for x in range(right + 1, size[0]) for y in range(size[1]))
            assert all(image.getpixel((x, y)) == background for y in range(top) for x in range(size[0]))
            assert all(image.getpixel((x, y)) == background for y in range(bottom + 1, size[1]) for x in range(size[0]))

def test_startup_logo_is_scaled_to_supported_three_color_panels():
    for size in ((212, 104), (250, 122)):
        image = StartupRenderer().render({}, {}, size)
        assert image.size == size
        assert image.mode == "P"
        assert set(image.tobytes()) <= {0, 1, 2}
        assert image.getpixel((0, 0)) == image.getpixel((size[0] - 1, size[1] - 1))
