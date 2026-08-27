"""Atomic local cache and display state."""
from __future__ import annotations
import json, os
from pathlib import Path
from typing import Any

class StateStore:
    def __init__(self, directory: str):
        self.directory = Path(directory); self.directory.mkdir(parents=True, exist_ok=True)
        self.path = self.directory / "state.json"
        self.data: dict[str, Any] = {}
        if self.path.exists():
            try: self.data = json.loads(self.path.read_text(encoding="utf-8"))
            except (OSError, ValueError): self.data = {}

    def save(self) -> None:
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(self.data, sort_keys=True), encoding="utf-8")
        os.replace(temporary, self.path)

    def cache_success(self, snapshot: dict, policy: dict, timestamp: float) -> None:
        self.data.update(snapshot=snapshot, policy=policy, last_success=timestamp, online=True)

    def cache_failure(self) -> None:
        self.data["online"] = False
