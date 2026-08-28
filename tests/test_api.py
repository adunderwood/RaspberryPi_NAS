import pytest
from nas_monitor.application import create_app
from nas_monitor.config import AppConfig
from nas_monitor.database import MetricStore

@pytest.fixture
def client(tmp_path):
    store = MetricStore(str(tmp_path / "metrics.sqlite3"))
    store.record("cpu.usage_percent", 25, "percent", "2026-01-01T00:00:00Z")
    store.record("cpu.temperature_c", 50, "celsius", "2026-01-01T00:00:01Z")
    store.record("ambient.temperature_c", 20, "celsius", "2026-01-01T00:00:02Z")
    array = {"device":"/dev/md0", "mount":"/mnt/nas", "bytes_total":10737418240,
             "bytes_used":5368709120, "bytes_free":5368709120, "usage_percent":50.0,
             "degraded_drives":0, "drives":[
                 {"device":"/dev/sda", "state":"in_sync", "errors":0, "healthy":True},
                 {"device":"/dev/sdb", "state":"in_sync", "errors":0, "healthy":True}]}
    app = create_app(AppConfig(), store, lambda: [array])
    app.testing = True
    with app.test_client() as test_client:
        yield test_client
    store.close()

def test_versioned_snapshot_is_typed(client):
    response = client.get("/api/v1/snapshot")
    assert response.status_code == 200
    assert response.json["cpu"]["usage_percent"] == 25
    assert response.json["storage"]["arrays"][0]["bytes_total"] == 10737418240

def test_dashboard_and_assets_are_served(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"System monitor" in response.data
    assert b"Approximate eInk display preview" in response.data
    assert b"Display theme" in response.data
    assert b"Drive health" in response.data
    assert b'id="cpu-temp-unit"' in response.data
    assert b'id="ambient-temp-unit"' in response.data
    assert client.get("/static/dashboard.css").status_code == 200
    assert client.get("/static/dashboard.js").status_code == 200

def test_event_stream_emits_typed_snapshot(client):
    response = client.get("/api/v1/events", buffered=False)
    first_event = next(response.response).decode()
    response.close()
    assert first_event.startswith("event: snapshot\ndata: ")
    assert '"schema_version":1' in first_event
    assert response.headers["Cache-Control"] == "no-cache"

def test_legacy_routes_remain_available(client):
    assert client.get("/cpu").json == {"cpu": [25.0]}
    assert client.get("/temperature").json == {"temperature": "68 F"}

def test_policy_validation_and_revision(client):
    policy = client.get("/api/v1/display/policy").json
    revision = policy["revision"]
    policy["theme"] = "dark"
    policy["fixed_screen"] = "drive_health"
    response = client.put("/api/v1/display/policy", json=policy)
    assert response.status_code == 200
    assert response.json["revision"] == revision + 1
    assert client.put("/api/v1/display/policy", json={"mode":"broken"}).status_code == 400
    policy["theme"] = "red"
    assert client.put("/api/v1/display/policy", json=policy).status_code == 400
    policy["theme"] = "dark"
    policy["screens"] = [{"type":"not-installed"}]
    assert client.put("/api/v1/display/policy", json=policy).status_code == 400
