from collections import namedtuple
from nas_monitor.collectors import collect_ambient_temperature, collect_storage, find_ambient_sensor
from nas_monitor.config import SensorConfig

def test_finds_and_reads_ds18b20_sensor(tmp_path):
    sensor = tmp_path / "28-000000000001" / "w1_slave"
    sensor.parent.mkdir()
    sensor.write_text("aa bb cc YES\naa bb t=23125\n")
    config = SensorConfig(one_wire_root=str(tmp_path))
    assert find_ambient_sensor(config) == sensor
    assert collect_ambient_temperature(sensor) == 23.125

def test_ignores_non_temperature_one_wire_devices(tmp_path):
    device = tmp_path / "w1_bus_master1" / "w1_slave"
    device.parent.mkdir()
    device.write_text("not a sensor")
    assert find_ambient_sensor(SensorConfig(one_wire_root=str(tmp_path))) is None

def test_storage_deduplicates_openmediavault_bind_mounts(monkeypatch):
    Partition = namedtuple("Partition", "device mountpoint")
    partitions = [
        Partition("/dev/md0", "/srv/dev-disk-by-uuid-array"),
        Partition("/dev/md0", "/export/photos"),
        Partition("/dev/md0", "/export/models"),
        Partition("/dev/mmcblk0p2", "/"),
    ]
    Usage = namedtuple("Usage", "total used free")
    monkeypatch.setattr("nas_monitor.collectors.psutil.disk_partitions", lambda all=False: partitions)
    monkeypatch.setattr("nas_monitor.collectors.shutil.disk_usage", lambda path: Usage(1000, 400, 600))

    assert collect_storage() == [{
        "device": "/dev/md0",
        "mount": "/srv/dev-disk-by-uuid-array",
        "bytes_total": 1000,
        "bytes_used": 400,
        "bytes_free": 600,
        "usage_percent": 40.0,
    }]
