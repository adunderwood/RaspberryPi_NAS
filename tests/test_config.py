import pytest
from nas_monitor.config import load_config

def test_loads_typed_toml(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[server]\nport=5100\n[database]\npath="/tmp/nas.db"\n')
    config = load_config(path)
    assert config.server.port == 5100
    assert config.database.path == "/tmp/nas.db"

def test_rejects_unknown_keys(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[server]\nporrt=5100\n')
    with pytest.raises(ValueError, match="porrt"):
        load_config(path)
