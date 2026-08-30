"""Flask application factory and compatibility API."""
from __future__ import annotations
import json
import time
from datetime import datetime, timezone
from typing import Any, Callable
from flask import Flask, Response, jsonify, render_template, request, stream_with_context
from .config import AppConfig
from .database import MetricStore
from .policy import SCREEN_TYPES, validate_policy

StorageProvider = Callable[[], list[dict[str, Any]]]

def create_app(config: AppConfig, store: MetricStore, storage_provider: StorageProvider) -> Flask:
    app = Flask(__name__)

    def build_snapshot() -> dict[str, Any]:
        cpu, cpu_temp = store.latest("cpu.usage_percent"), store.latest("cpu.temperature_c")
        memory = store.latest("memory.usage_percent")
        ambient = store.latest("ambient.temperature_c")
        stamps = [item["collected_at"] for item in (cpu, cpu_temp, memory, ambient) if item]
        return {
            "schema_version": 1, "collected_at": max(stamps) if stamps else None,
            "status": "ok" if cpu else "starting",
            "cpu": {"usage_percent": cpu["value"] if cpu else None,
                    "temperature_c": cpu_temp["value"] if cpu_temp else None,
                    "usage_history": store.series("cpu.usage_percent", config.collection.history_points),
                    "temperature_history": store.series("cpu.temperature_c", config.collection.history_points)},
            "memory": {"usage_percent": memory["value"] if memory else None,
                       "usage_history": store.series("memory.usage_percent", config.collection.history_points)},
            "ambient": {"temperature_c": ambient["value"] if ambient else None},
            "storage": {"arrays": storage_provider()},
        }

    @app.get("/")
    def index(): return render_template("dashboard.html")

    @app.get("/api/v1")
    def api_index():
        return jsonify({"service": "NAS Monitoring Service", "schema_version": 1,
                        "endpoints": ["/api/v1/health", "/api/v1/snapshot",
                                      "/api/v1/events", "/api/v1/display/policy",
                                      "/api/v1/display/show"]})

    @app.get("/api/v1/health")
    def health():
        return jsonify({"status": "ok", "time": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")})

    @app.get("/api/v1/snapshot")
    def snapshot(): return jsonify(build_snapshot())

    @app.get("/api/v1/events")
    def events():
        @stream_with_context
        def generate():
            while True:
                yield f"event: snapshot\ndata: {json.dumps(build_snapshot(), separators=(',', ':'))}\n\n"
                time.sleep(3)
        response = Response(generate(), mimetype="text/event-stream")
        response.headers["Cache-Control"] = "no-cache"
        response.headers["X-Accel-Buffering"] = "no"
        return response

    @app.get("/api/v1/display/policy")
    def get_policy(): return jsonify(store.get_policy())

    @app.put("/api/v1/display/policy")
    def put_policy():
        try:
            policy = validate_policy(request.get_json(silent=False))
        except (ValueError, TypeError) as error:
            return jsonify({"error": str(error)}), 400
        return jsonify(store.set_policy(policy))

    @app.post("/api/v1/display/show")
    def show_display():
        body = request.get_json(silent=True) or {}
        screen, theme, unit = body.get("screen"), body.get("theme"), body.get("temperature_unit")
        if screen not in SCREEN_TYPES:
            return jsonify({"error": "invalid screen"}), 400
        if theme not in {"light", "dark"}:
            return jsonify({"error": "invalid theme"}), 400
        if unit not in {"C", "F"}:
            return jsonify({"error": "temperature_unit must be C or F"}), 400
        return jsonify(store.request_display(screen, theme, unit))

    @app.get("/cpu")
    def legacy_cpu():
        return jsonify({"cpu": [x["value"] for x in store.series("cpu.usage_percent", config.collection.history_points)]})

    @app.get("/cpu_temp")
    def legacy_cpu_temp():
        return jsonify({"cpu_temp": [x["value"] for x in store.series("cpu.temperature_c", config.collection.history_points)]})

    @app.get("/temperature")
    def legacy_temperature():
        reading = store.latest("ambient.temperature_c")
        if not reading: return jsonify({"temperature": "ERROR"})
        unit = store.get_policy()["temperature_unit"]
        value = reading["value"] if unit == "C" else reading["value"] * 9 / 5 + 32
        return jsonify({"temperature": f"{value:.0f} {unit}"})

    @app.get("/raid")
    def legacy_raid():
        arrays = storage_provider()
        if not arrays: return jsonify({"error": "No RAID arrays found"}), 404
        array, gib = arrays[0], 1024 ** 3
        return jsonify({"device": array["device"], "mount": array["mount"],
                        "total": f"{array['bytes_total']/gib:.1f}G", "used": f"{array['bytes_used']/gib:.1f}G",
                        "free": f"{array['bytes_free']/gib:.1f}G", "percent": f"{array['usage_percent']:.0f}%"})
    return app
