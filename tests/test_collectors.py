from nas_monitor.collectors import collect_ambient_temperature, find_ambient_sensor
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
