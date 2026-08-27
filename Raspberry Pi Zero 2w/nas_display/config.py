"""Minimal local configuration for the display controller."""
from __future__ import annotations
import os, tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

DEFAULT_CONFIG_PATH = Path("/etc/nas-display/config.toml")

@dataclass(frozen=True)
class DisplayConfig:
    server_url: str = "http://10.99.0.1:5000"
    connect_timeout_seconds: float = 3.0
    read_timeout_seconds: float = 5.0
    poll_interval_seconds: float = 30.0
    state_directory: str = "/var/lib/nas-display"

def normalize_server(value: str) -> str:
    value = value.strip().rstrip("/")
    if not value:
        raise ValueError("server address cannot be empty")
    if "://" not in value:
        value = f"http://{value}"
    parsed = urlsplit(value)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("server address must be a hostname, IP address, or HTTP(S) URL")
    if parsed.path not in {"", "/"} or parsed.query or parsed.fragment:
        raise ValueError("server address cannot contain a path, query, or fragment")
    netloc = parsed.netloc if parsed.port else f"{parsed.hostname}:5000"
    return urlunsplit((parsed.scheme, netloc, "", "", ""))

def load_config(path: str | Path | None = None) -> DisplayConfig:
    config_path = Path(path or os.environ.get("NAS_DISPLAY_CONFIG", DEFAULT_CONFIG_PATH))
    raw = {}
    if config_path.exists():
        with config_path.open("rb") as stream: raw = tomllib.load(stream)
    unknown_sections = set(raw) - {"server", "agent"}
    if unknown_sections: raise ValueError(f"unknown configuration sections: {', '.join(sorted(unknown_sections))}")
    server, agent = raw.get("server", {}), raw.get("agent", {})
    if set(server) - {"address", "connect_timeout_seconds", "read_timeout_seconds"}:
        raise ValueError("unknown key in [server]")
    if set(agent) - {"poll_interval_seconds", "state_directory"}:
        raise ValueError("unknown key in [agent]")
    config = DisplayConfig(
        server_url=normalize_server(server.get("address", "10.99.0.1")),
        connect_timeout_seconds=float(server.get("connect_timeout_seconds", 3)),
        read_timeout_seconds=float(server.get("read_timeout_seconds", 5)),
        poll_interval_seconds=float(agent.get("poll_interval_seconds", 30)),
        state_directory=str(agent.get("state_directory", "/var/lib/nas-display")),
    )
    if min(config.connect_timeout_seconds, config.read_timeout_seconds, config.poll_interval_seconds) <= 0:
        raise ValueError("timeouts and poll interval must be greater than zero")
    return config
