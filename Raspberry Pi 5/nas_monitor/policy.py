"""Display policy validation."""
from typing import Any
from .database import DEFAULT_POLICY

SCREEN_TYPES = {"overview", "storage", "thermal", "drive_health", "cpu_memory"}

def validate_policy(candidate: Any) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("policy must be a JSON object")
    unknown = set(candidate) - set(DEFAULT_POLICY) - {"revision", "updated_at"}
    if unknown:
        raise ValueError(f"unknown policy keys: {', '.join(sorted(unknown))}")
    policy = dict(DEFAULT_POLICY)
    policy.update({k: v for k, v in candidate.items() if k not in {"revision", "updated_at"}})
    if policy["mode"] not in {"fixed", "rotate"}: raise ValueError("mode must be fixed or rotate")
    if policy["theme"] not in {"light", "dark"}: raise ValueError("invalid theme")
    if policy["temperature_unit"] not in {"C", "F"}: raise ValueError("temperature_unit must be C or F")
    if policy["fixed_screen"] not in SCREEN_TYPES: raise ValueError("invalid fixed_screen")
    if not isinstance(policy["screens"], list) or not policy["screens"]: raise ValueError("screens cannot be empty")
    if any(not isinstance(s, dict) or not isinstance(s.get("type"), str) for s in policy["screens"]):
        raise ValueError("each screen requires a string type")
    invalid_screens = {screen["type"] for screen in policy["screens"]} - SCREEN_TYPES
    if invalid_screens: raise ValueError(f"unsupported screens: {', '.join(sorted(invalid_screens))}")
    for key in ("rotation_interval_seconds", "refresh_interval_seconds"):
        if not isinstance(policy[key], int) or policy[key] < 60:
            raise ValueError(f"{key} must be at least 60 seconds")
    thresholds = policy.get("thresholds")
    if not isinstance(thresholds, dict): raise ValueError("thresholds must be an object")
    expected_thresholds = {"storage_percent", "cpu_temperature_c", "ambient_temperature_c"}
    if set(thresholds) != expected_thresholds: raise ValueError("thresholds contains invalid keys")
    if not 1 <= thresholds["storage_percent"] <= 100: raise ValueError("storage threshold must be 1-100")
    if not 1 <= thresholds["cpu_temperature_c"] <= 120: raise ValueError("CPU threshold must be 1-120")
    if not 1 <= thresholds["ambient_temperature_c"] <= 100: raise ValueError("ambient threshold must be 1-100")
    return policy
