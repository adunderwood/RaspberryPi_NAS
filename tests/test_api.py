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
             "bytes_used":5368709120, "bytes_free":5368709120, "usage_percent":50.0}
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

def test_legacy_routes_remain_available(client):
    assert client.get("/cpu").json == {"cpu": [25.0]}
    assert client.get("/temperature").json == {"temperature": "68 F"}

def test_policy_validation_and_revision(client):
    policy = client.get("/api/v1/display/policy").json
    revision = policy["revision"]
    policy["theme"] = "dark"
    response = client.put("/api/v1/display/policy", json=policy)
    assert response.status_code == 200
    assert response.json["revision"] == revision + 1
    assert client.put("/api/v1/display/policy", json={"mode":"broken"}).status_code == 400
