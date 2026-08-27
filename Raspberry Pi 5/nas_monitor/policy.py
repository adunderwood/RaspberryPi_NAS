"""Display policy validation."""
from typing import Any
from .database import DEFAULT_POLICY

def validate_policy(candidate: Any) -> dict[str, Any]:
    if not isinstance(candidate, dict):
        raise ValueError("policy must be a JSON object")
    unknown = set(candidate) - set(DEFAULT_POLICY) - {"revision", "updated_at"}
    if unknown:
        raise ValueError(f"unknown policy keys: {', '.join(sorted(unknown))}")
    policy = dict(DEFAULT_POLICY)
    policy.update({k: v for k, v in candidate.items() if k not in {"revision", "updated_at"}})
    if policy["mode"] not in {"fixed", "rotate"}: raise ValueError("mode must be fixed or rotate")
    if policy["theme"] not in {"light", "dark", "red"}: raise ValueError("invalid theme")
    if policy["temperature_unit"] not in {"C", "F"}: raise ValueError("temperature_unit must be C or F")
    if not isinstance(policy["screens"], list) or not policy["screens"]: raise ValueError("screens cannot be empty")
    if any(not isinstance(s, dict) or not isinstance(s.get("type"), str) for s in policy["screens"]):
        raise ValueError("each screen requires a string type")
    for key in ("rotation_interval_seconds", "refresh_interval_seconds"):
        if not isinstance(policy[key], int) or policy[key] < 60:
            raise ValueError(f"{key} must be at least 60 seconds")
    return policy
