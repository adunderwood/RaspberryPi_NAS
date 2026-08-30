from nas_monitor.database import MetricStore

def test_metrics_and_policy_are_persistent(tmp_path):
    path = tmp_path / "metrics.sqlite3"
    store = MetricStore(str(path))
    store.record("cpu.usage_percent", 12.5, "percent", "2026-01-01T00:00:00Z")
    assert store.latest("cpu.usage_percent")["value"] == 12.5
    revision = store.get_policy()["revision"]
    policy = store.get_policy(); policy["theme"] = "dark"
    assert store.set_policy(policy)["revision"] == revision + 1
    store.close()
    reopened = MetricStore(str(path))
    assert reopened.get_policy()["theme"] == "dark"
    reopened.close()

def test_legacy_display_defaults_are_migrated(tmp_path):
    path = tmp_path / "metrics.sqlite3"
    store = MetricStore(str(path))
    policy = store.get_policy(); policy["theme"] = "red"
    policy["thresholds"]["ambient_temperature_c"] = 35
    legacy_revision = store.set_policy(policy)["revision"]
    store.close()

    reopened = MetricStore(str(path))
    migrated = reopened.get_policy()
    assert migrated["theme"] == "light"
    assert migrated["thresholds"]["ambient_temperature_c"] == 37.8
    assert migrated["revision"] == legacy_revision + 1
    reopened.close()

def test_bucketed_series_averages_raw_samples(tmp_path):
    store = MetricStore(str(tmp_path / "metrics.sqlite3"))
    try:
        store.record("cpu.usage_percent", 10, "percent", "2026-01-01T00:00:01Z")
        store.record("cpu.usage_percent", 30, "percent", "2026-01-01T00:00:30Z")
        store.record("cpu.usage_percent", 50, "percent", "2026-01-01T00:01:01Z")
        points = store.bucketed_series("cpu.usage_percent", 60, 18)
        assert [point["value"] for point in points] == [20, 50]
    finally:
        store.close()
