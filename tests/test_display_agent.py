from PIL import Image
from nas_display.agent import DisplayAgent, image_hash, is_alert, selected_screen
from nas_display.client import ApiError
from nas_display.state import StateStore

POLICY = {
    "mode":"fixed", "fixed_screen":"overview", "screens":[{"type":"overview"}],
    "rotation_interval_seconds":300, "refresh_interval_seconds":300,
    "theme":"light", "temperature_unit":"F", "revision":1,
    "offline_screen":True, "refresh_on_alert":True,
    "thresholds":{"storage_percent":90,"cpu_temperature_c":80,"ambient_temperature_c":35},
}
SNAPSHOT = {
    "schema_version":1, "status":"ok", "cpu":{"usage_percent":10,"temperature_c":50,"usage_history":[]},
    "ambient":{"temperature_c":25}, "storage":{"arrays":[{"usage_percent":40,"bytes_total":1000,
    "bytes_used":400,"bytes_free":600}]},
}

class FakeClient:
    def __init__(self): self.offline = False
    def snapshot(self):
        if self.offline: raise ApiError("offline")
        return SNAPSHOT
    def policy(self): return POLICY

class FakeHardware:
    size = (212, 104)
    def __init__(self): self.images = []
    def show(self, image): self.images.append(image.copy())

def test_hash_changes_with_pixels():
    first, second = Image.new("P", (2, 2), 0), Image.new("P", (2, 2), 0)
    second.putpixel((0, 0), 1)
    assert image_hash(first) != image_hash(second)

def test_rotation_is_deterministic():
    policy = {"mode":"rotate", "rotation_interval_seconds":60,
              "screens":[{"type":"overview"},{"type":"thermal"}]}
    assert selected_screen(policy, 0)["type"] == "overview"
    assert selected_screen(policy, 60)["type"] == "thermal"

def test_degraded_drive_triggers_alert_refresh():
    snapshot = {**SNAPSHOT, "storage":{"arrays":[{
        "usage_percent":40, "degraded_drives":1,
        "drives":[{"device":"/dev/sda", "state":"faulty", "healthy":False}]}]}}
    assert is_alert(snapshot, POLICY) is True

def test_agent_suppresses_unneeded_and_repeated_offline_refreshes(tmp_path):
    now = [1000.0]; client, hardware = FakeClient(), FakeHardware()
    agent = DisplayAgent(client, StateStore(str(tmp_path)), hardware, clock=lambda: now[0])
    assert agent.run_once() is True
    assert len(hardware.images) == 1
    now[0] += 30
    assert agent.run_once() is False
    assert len(hardware.images) == 1
    client.offline = True; now[0] += 30
    assert agent.run_once() is True
    assert len(hardware.images) == 2
    now[0] += 30
    assert agent.run_once() is False
    assert len(hardware.images) == 2
    client.offline = False; now[0] += 30
    assert agent.run_once() is True
    assert len(hardware.images) == 3
