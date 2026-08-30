"""SQLite persistence for metrics and display policy."""
from __future__ import annotations
import json, sqlite3, threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEFAULT_POLICY: dict[str, Any] = {
    "mode": "rotate", "fixed_screen": "overview", "screens": [{"type": "overview"}],
    "rotation_interval_seconds": 300, "refresh_interval_seconds": 300,
    "cpu_bucket_seconds": 300, "refresh_on_alert": True, "offline_screen": True,
    "daily_cleanup": {"enabled": True, "time": "03:00"},
    "thresholds": {"storage_percent": 90, "cpu_temperature_c": 80, "ambient_temperature_c": 37.8},
    "theme": "light", "temperature_unit": "F",
}

class MetricStore:
    def __init__(self, path: str, retention_days: int = 30):
        self.path, self.retention_days = path, retention_days
        self._lock = threading.RLock()
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self._connection = sqlite3.connect(path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        with self._connection:
            self._connection.executescript("""
              PRAGMA journal_mode=WAL;
              CREATE TABLE IF NOT EXISTS metric_samples (
                id INTEGER PRIMARY KEY, collected_at TEXT NOT NULL, name TEXT NOT NULL,
                value REAL NOT NULL, unit TEXT NOT NULL);
              CREATE INDEX IF NOT EXISTS metric_samples_name_time ON metric_samples(name, collected_at DESC);
              CREATE TABLE IF NOT EXISTS application_state (
                key TEXT PRIMARY KEY, value TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL);
            """)
            self._connection.execute(
                "INSERT OR IGNORE INTO application_state(key,value,revision,updated_at) VALUES(?,?,1,?)",
                ("display_policy", json.dumps(DEFAULT_POLICY), self.now()))
            row = self._connection.execute(
                "SELECT value FROM application_state WHERE key='display_policy'").fetchone()
            stored_policy = json.loads(row["value"])
            migrated = False
            if stored_policy.get("theme") == "red":
                stored_policy["theme"] = "light"
                migrated = True
            thresholds = stored_policy.get("thresholds", {})
            if thresholds.get("ambient_temperature_c") == 35:
                thresholds["ambient_temperature_c"] = 37.8
                migrated = True
            if migrated:
                self._connection.execute(
                    "UPDATE application_state SET value=?,revision=revision+1,updated_at=? WHERE key='display_policy'",
                    (json.dumps(stored_policy), self.now()))

    @staticmethod
    def now() -> str:
        return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    def record(self, name: str, value: float, unit: str, collected_at: str | None = None) -> None:
        with self._lock, self._connection:
            self._connection.execute("INSERT INTO metric_samples(collected_at,name,value,unit) VALUES(?,?,?,?)",
                                     (collected_at or self.now(), name, float(value), unit))

    def series(self, name: str, limit: int) -> list[dict[str, Any]]:
        with self._lock:
            rows = self._connection.execute(
                "SELECT collected_at,value,unit FROM metric_samples WHERE name=? ORDER BY collected_at DESC LIMIT ?",
                (name, limit)).fetchall()
        return [dict(row) for row in reversed(rows)]

    def latest(self, name: str) -> dict[str, Any] | None:
        values = self.series(name, 1)
        return values[0] if values else None

    def get_policy(self) -> dict[str, Any]:
        with self._lock:
            row = self._connection.execute(
                "SELECT value,revision,updated_at FROM application_state WHERE key='display_policy'").fetchone()
        result = json.loads(row["value"])
        result.update(revision=row["revision"], updated_at=row["updated_at"])
        return result

    def set_policy(self, policy: dict[str, Any]) -> dict[str, Any]:
        clean = {key: value for key, value in policy.items() if key not in {"revision", "updated_at"}}
        with self._lock, self._connection:
            self._connection.execute(
                "UPDATE application_state SET value=?,revision=revision+1,updated_at=? WHERE key='display_policy'",
                (json.dumps(clean), self.now()))
        return self.get_policy()

    def request_display(self, screen: str, theme: str, temperature_unit: str) -> dict[str, Any]:
        """Request a temporary screen without changing fixed/rotation preferences."""
        policy = self.get_policy()
        hold_seconds = max(60, int(policy.get("rotation_interval_seconds", 300)))
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=hold_seconds)
        policy["display_override"] = {
            "type": screen,
            "theme": theme,
            "temperature_unit": temperature_unit,
            "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
        }
        return self.set_policy(policy)

    def prune(self) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=self.retention_days)).isoformat().replace("+00:00", "Z")
        with self._lock, self._connection:
            cursor = self._connection.execute("DELETE FROM metric_samples WHERE collected_at < ?", (cutoff,))
        return cursor.rowcount

    def close(self) -> None:
        with self._lock:
            self._connection.close()
