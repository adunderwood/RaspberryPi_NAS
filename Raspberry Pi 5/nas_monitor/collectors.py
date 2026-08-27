"""Hardware metric collectors."""
from __future__ import annotations
import shutil
from pathlib import Path
from typing import Any
import psutil
from .config import SensorConfig

def collect_cpu_usage() -> float:
    return float(psutil.cpu_percent(interval=None))

def collect_cpu_temperature(path: str) -> float:
    return int(Path(path).read_text(encoding="utf-8").strip()) / 1000.0

def find_ambient_sensor(config: SensorConfig) -> Path | None:
    root = Path(config.one_wire_root)
    if config.ambient_sensor_id != "auto":
        candidate = root / config.ambient_sensor_id / "w1_slave"
        return candidate if candidate.exists() else None
    return next(iter(sorted(root.glob("28-*/w1_slave"))), None)

def collect_ambient_temperature(sensor_path: Path) -> float:
    lines = sensor_path.read_text(encoding="utf-8").splitlines()
    if len(lines) < 2 or not lines[0].strip().endswith("YES") or "t=" not in lines[1]:
        raise ValueError("DS18B20 reading failed CRC validation")
    return int(lines[1].rsplit("t=", 1)[1]) / 1000.0

def collect_md_members(device: str, sys_block_root: Path = Path("/sys/class/block")) -> tuple[list[dict[str, Any]], int]:
    """Read Linux MD member state without requiring privileged SMART access."""
    md_root = sys_block_root / Path(device).name / "md"
    try:
        degraded = int((md_root / "degraded").read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        degraded = 0
    members = []
    for member in sorted(md_root.glob("dev-*")):
        state_path = member / "state"
        try:
            state = state_path.read_text(encoding="utf-8").strip()
        except OSError:
            state = "unknown"
        try:
            errors = int((member / "errors").read_text(encoding="utf-8").strip())
        except (OSError, ValueError):
            errors = 0
        name = member.name.removeprefix("dev-").replace("!", "/")
        healthy = state in {"active", "in_sync", "write_mostly"} and errors == 0
        members.append({"device": f"/dev/{name}", "state": state, "errors": errors, "healthy": healthy})
    return members, degraded

def collect_storage() -> list[dict[str, Any]]:
    arrays = []
    seen_devices: set[str] = set()
    for partition in psutil.disk_partitions(all=False):
        # OpenMediaVault exposes shared folders as bind mounts. psutil reports
        # each bind mount as another partition backed by the same md device, but
        # the API models arrays rather than mount aliases.
        if partition.device.startswith("/dev/md") and partition.device not in seen_devices:
            seen_devices.add(partition.device)
            usage = shutil.disk_usage(partition.mountpoint)
            drives, degraded = collect_md_members(partition.device)
            arrays.append({"device": partition.device, "mount": partition.mountpoint,
                           "bytes_total": usage.total, "bytes_used": usage.used, "bytes_free": usage.free,
                           "usage_percent": round(usage.used / usage.total * 100 if usage.total else 0, 1),
                           "degraded_drives": degraded, "drives": drives})
    return arrays
