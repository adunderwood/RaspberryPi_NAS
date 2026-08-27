"""Long-running display agent with cached offline behavior."""
from __future__ import annotations
import hashlib, logging, signal, time
from typing import Any
from .client import ApiError, NasClient
from .config import load_config
from .display import InkyHardware
from .renderers import get_renderer
from .state import StateStore

LOGGER = logging.getLogger(__name__)
FALLBACK_POLICY = {
    "mode": "fixed", "fixed_screen": "overview", "screens": [{"type": "overview"}],
    "rotation_interval_seconds": 300, "refresh_interval_seconds": 300,
    "theme": "light", "temperature_unit": "F", "revision": 0,
    "offline_screen": True, "refresh_on_alert": True,
    "thresholds": {"storage_percent": 90, "cpu_temperature_c": 80, "ambient_temperature_c": 35},
}

def image_hash(image) -> str:
    digest = hashlib.sha256()
    digest.update(f"{image.mode}:{image.size}".encode())
    digest.update(image.tobytes())
    return digest.hexdigest()

def selected_screen(policy: dict[str, Any], now: float) -> dict[str, Any]:
    if policy.get("mode") == "fixed": return {"type": policy.get("fixed_screen", "overview")}
    screens = policy.get("screens") or [{"type": "overview"}]
    interval = max(60, int(policy.get("rotation_interval_seconds", 300)))
    return screens[int(now // interval) % len(screens)]

def is_alert(snapshot: dict[str, Any], policy: dict[str, Any]) -> bool:
    thresholds = policy.get("thresholds", {})
    arrays = snapshot.get("storage", {}).get("arrays", [])
    storage_alert = any(float(item.get("usage_percent", 0)) >= float(thresholds.get("storage_percent", 90)) for item in arrays)
    drive_alert = any(int(item.get("degraded_drives", 0) or 0) > 0 or
                      any(not drive.get("healthy", False) for drive in item.get("drives", []))
                      for item in arrays)
    cpu_temp = snapshot.get("cpu", {}).get("temperature_c")
    ambient = snapshot.get("ambient", {}).get("temperature_c")
    return (storage_alert or drive_alert or
            (cpu_temp is not None and cpu_temp >= float(thresholds.get("cpu_temperature_c", 80))) or
            (ambient is not None and ambient >= float(thresholds.get("ambient_temperature_c", 35))))

class DisplayAgent:
    def __init__(self, client: NasClient, state: StateStore, hardware, clock=time.time):
        self.client, self.state, self.hardware, self.clock = client, state, hardware, clock

    def _show_if_needed(self, image, force: bool = False) -> bool:
        fingerprint = image_hash(image)
        if not force and fingerprint == self.state.data.get("image_hash"): return False
        self.hardware.show(image)
        self.state.data.update(image_hash=fingerprint, last_show=self.clock())
        self.state.save()
        return True

    def run_once(self) -> bool:
        now = self.clock()
        cached_policy = self.state.data.get("policy") or FALLBACK_POLICY
        try:
            snapshot = self.client.snapshot()
        except ApiError as error:
            LOGGER.warning("Monitoring service unavailable: %s", error)
            was_online = self.state.data.get("online", True)
            self.state.cache_failure()
            if not cached_policy.get("offline_screen", True): return False
            offline_data = {"last_success": self.state.data.get("last_success")}
            image = get_renderer("offline").render(offline_data, cached_policy, self.hardware.size)
            shown = self._show_if_needed(image, force=was_online)
            if shown: LOGGER.info("Displayed offline screen")
            return shown

        try: policy = self.client.policy()
        except ApiError as error:
            LOGGER.warning("Using cached display policy: %s", error)
            policy = cached_policy

        old_revision = self.state.data.get("policy", {}).get("revision")
        old_alert = self.state.data.get("alert", False)
        old_screen = self.state.data.get("screen")
        was_online = self.state.data.get("online", False)
        alert = is_alert(snapshot, policy)
        screen = selected_screen(policy, now)
        self.state.cache_success(snapshot, policy, now)
        renderer = get_renderer(screen.get("type", "overview"))
        image = renderer.render(snapshot, policy, self.hardware.size)
        last_show = float(self.state.data.get("last_show", 0))
        due = now - last_show >= float(policy.get("refresh_interval_seconds", 300))
        urgent = (not was_online or old_revision != policy.get("revision") or old_screen != screen or
                  (policy.get("refresh_on_alert", True) and alert != old_alert))
        self.state.data.update(alert=alert, screen=screen)
        if not (due or urgent): return False
        shown = self._show_if_needed(image)
        if shown: LOGGER.info("Displayed %s screen", renderer.name)
        return shown

def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load_config(); state = StateStore(config.state_directory); hardware = InkyHardware()
    LOGGER.info("Display agent started: server=%s panel=%sx%s", config.server_url, *hardware.size)
    agent = DisplayAgent(NasClient(config), state, hardware)
    stopping = False
    def stop(_signum, _frame):
        nonlocal stopping; stopping = True
    signal.signal(signal.SIGTERM, stop); signal.signal(signal.SIGINT, stop)
    while not stopping:
        try: agent.run_once()
        except Exception: LOGGER.exception("Display update failed")
        end = time.monotonic() + config.poll_interval_seconds
        while not stopping and time.monotonic() < end: time.sleep(min(1, end - time.monotonic()))
