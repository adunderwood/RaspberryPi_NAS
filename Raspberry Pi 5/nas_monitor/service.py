"""Service lifecycle and metric scheduling."""
import logging, signal, threading, time
from waitress import serve
from .application import create_app
from .collectors import collect_ambient_temperature, collect_cpu_temperature, collect_cpu_usage, collect_storage, find_ambient_sensor
from .config import AppConfig, load_config
from .database import MetricStore

LOGGER = logging.getLogger(__name__)

class CollectorService:
    def __init__(self, config: AppConfig, store: MetricStore):
        self.config, self.store = config, store
        self.stop_event, self.threads = threading.Event(), []

    def _run(self, name, unit, interval, collector):
        while not self.stop_event.is_set():
            started = time.monotonic()
            try: self.store.record(name, collector(), unit)
            except Exception: LOGGER.exception("Failed to collect %s", name)
            self.stop_event.wait(max(0, interval - (time.monotonic() - started)))

    def start(self):
        collect_cpu_usage()
        jobs = [
            ("cpu.usage_percent", "percent", self.config.collection.cpu_interval_seconds, collect_cpu_usage),
            ("cpu.temperature_c", "celsius", self.config.collection.temperature_interval_seconds,
             lambda: collect_cpu_temperature(self.config.sensors.cpu_temperature_path))]
        def ambient_temperature():
            # One-wire devices can appear after the service starts. Resolve the
            # sensor for every attempt so a boot-time race heals automatically.
            sensor = find_ambient_sensor(self.config.sensors)
            if sensor is None:
                raise FileNotFoundError(
                    f"No DS18B20 sensor under {self.config.sensors.one_wire_root}"
                )
            return collect_ambient_temperature(sensor)

        jobs.append(("ambient.temperature_c", "celsius", self.config.collection.temperature_interval_seconds,
                     ambient_temperature))
        for job in jobs:
            thread = threading.Thread(target=self._run, args=job, daemon=True, name=job[0])
            thread.start(); self.threads.append(thread)

    def stop(self):
        self.stop_event.set()
        for thread in self.threads: thread.join(timeout=5)

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    config = load_config()
    store = MetricStore(config.database.path, config.database.retention_days)
    collectors = CollectorService(config, store); collectors.start()
    def shutdown(_signum, _frame):
        collectors.stop(); store.close(); raise SystemExit(0)
    signal.signal(signal.SIGTERM, shutdown); signal.signal(signal.SIGINT, shutdown)
    serve(create_app(config, store, collect_storage), host=config.server.host, port=config.server.port, threads=4)
