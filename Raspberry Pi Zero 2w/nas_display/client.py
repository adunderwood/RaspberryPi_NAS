"""Typed-enough HTTP client for the versioned NAS API."""
from __future__ import annotations
from typing import Any
import requests
from .config import DisplayConfig

class ApiError(RuntimeError): pass

class NasClient:
    def __init__(self, config: DisplayConfig, session: requests.Session | None = None):
        self.config, self.session = config, session or requests.Session()

    def _get(self, path: str) -> dict[str, Any]:
        try:
            response = self.session.get(
                f"{self.config.server_url}{path}",
                timeout=(self.config.connect_timeout_seconds, self.config.read_timeout_seconds))
            response.raise_for_status()
            data = response.json()
        except (requests.RequestException, ValueError) as error:
            raise ApiError(str(error)) from error
        if not isinstance(data, dict): raise ApiError("server returned a non-object JSON response")
        return data

    def snapshot(self) -> dict[str, Any]:
        data = self._get("/api/v1/snapshot")
        if data.get("schema_version") != 1 or not isinstance(data.get("cpu"), dict):
            raise ApiError("unsupported or malformed snapshot")
        return data

    def policy(self) -> dict[str, Any]:
        data = self._get("/api/v1/display/policy")
        required = {"mode", "screens", "refresh_interval_seconds", "revision", "theme", "temperature_unit"}
        if not required.issubset(data): raise ApiError("malformed display policy")
        return data
