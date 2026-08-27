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
