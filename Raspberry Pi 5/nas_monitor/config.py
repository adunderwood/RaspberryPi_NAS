"""Typed application configuration loaded from TOML."""
from __future__ import annotations
import os, tomllib
from dataclasses import dataclass, fields
from pathlib import Path
from typing import Any, TypeVar

DEFAULT_CONFIG_PATH = Path("/etc/nas-monitor/config.toml")
T = TypeVar("T")

@dataclass(frozen=True)
class ServerConfig:
    host: str = "0.0.0.0"
    port: int = 5000

@dataclass(frozen=True)
class DatabaseConfig:
    path: str = "/var/lib/nas-monitor/metrics.sqlite3"
    retention_days: int = 30

@dataclass(frozen=True)
class CollectionConfig:
    cpu_interval_seconds: float = 3.0
    temperature_interval_seconds: float = 10.0
    storage_interval_seconds: float = 60.0
    history_points: int = 18

@dataclass(frozen=True)
class SensorConfig:
    cpu_temperature_path: str = "/sys/class/thermal/thermal_zone0/temp"
    one_wire_root: str = "/sys/bus/w1/devices"
    ambient_sensor_id: str = "auto"

@dataclass(frozen=True)
class AppConfig:
    server: ServerConfig = ServerConfig()
    database: DatabaseConfig = DatabaseConfig()
    collection: CollectionConfig = CollectionConfig()
    sensors: SensorConfig = SensorConfig()

def _section(kind: type[T], values: dict[str, Any], name: str) -> T:
    allowed = {field.name for field in fields(kind)}
    unknown = set(values) - allowed
    if unknown:
        raise ValueError(f"Unknown keys in [{name}]: {', '.join(sorted(unknown))}")
    return kind(**values)

def load_config(path: str | Path | None = None) -> AppConfig:
    config_path = Path(path or os.environ.get("NAS_MONITOR_CONFIG", DEFAULT_CONFIG_PATH))
    raw: dict[str, Any] = {}
    if config_path.exists():
        with config_path.open("rb") as stream:
            raw = tomllib.load(stream)
    unknown = set(raw) - {"server", "database", "collection", "sensors"}
    if unknown:
        raise ValueError(f"Unknown configuration sections: {', '.join(sorted(unknown))}")
    config = AppConfig(
        server=_section(ServerConfig, raw.get("server", {}), "server"),
        database=_section(DatabaseConfig, raw.get("database", {}), "database"),
        collection=_section(CollectionConfig, raw.get("collection", {}), "collection"),
        sensors=_section(SensorConfig, raw.get("sensors", {}), "sensors"),
    )
    if not 1 <= config.server.port <= 65535:
        raise ValueError("server.port must be between 1 and 65535")
    if config.database.retention_days < 1 or config.collection.history_points < 1:
        raise ValueError("retention_days and history_points must be positive")
    intervals = (config.collection.cpu_interval_seconds, config.collection.temperature_interval_seconds,
                 config.collection.storage_interval_seconds)
    if any(value <= 0 for value in intervals):
        raise ValueError("collection intervals must be greater than zero")
    return config
