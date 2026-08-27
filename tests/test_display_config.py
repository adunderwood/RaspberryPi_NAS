import pytest
from nas_display.config import load_config, normalize_server

def test_normalizes_hostname_ip_and_explicit_url():
    assert normalize_server("10.99.0.1") == "http://10.99.0.1:5000"
    assert normalize_server("nas.local") == "http://nas.local:5000"
    assert normalize_server("https://nas.example:8443/") == "https://nas.example:8443"

def test_rejects_server_paths():
    with pytest.raises(ValueError, match="path"):
        normalize_server("http://nas.local/api")

def test_loads_single_address_config(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[server]\naddress="nas.local"\n[agent]\npoll_interval_seconds=15\n')
    config = load_config(path)
    assert config.server_url == "http://nas.local:5000"
    assert config.poll_interval_seconds == 15
