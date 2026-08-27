#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this installer with sudo." >&2
  exit 1
fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH= cd -- "$script_dir/../.." && pwd)
app_source="$repo_dir/Raspberry Pi 5"

command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
command -v systemctl >/dev/null || { echo "systemd is required" >&2; exit 1; }
command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }

if ! id nas-monitor >/dev/null 2>&1; then
  useradd --system --home /var/lib/nas-monitor --shell /usr/sbin/nologin nas-monitor
fi

install -d -m 0755 /opt/nas-monitor /etc/nas-monitor
install -d -o nas-monitor -g nas-monitor -m 0750 /var/lib/nas-monitor

# Replace application-owned files while preserving the virtual environment and state elsewhere.
find /opt/nas-monitor -mindepth 1 -maxdepth 1 ! -name .venv -exec rm -rf -- {} +
cp -a "$app_source/nas_monitor" /opt/nas-monitor/
install -m 0755 "$app_source/nas_service.py" /opt/nas-monitor/nas_service.py
install -m 0644 "$app_source/requirements.txt" /opt/nas-monitor/requirements.txt
install -m 0755 "$script_dir/uninstall-pi5.sh" /opt/nas-monitor/uninstall-pi5.sh

if [ ! -f /etc/nas-monitor/config.toml ]; then
  install -m 0644 "$repo_dir/config/pi5.example.toml" /etc/nas-monitor/config.toml
fi

if [ ! -x /opt/nas-monitor/.venv/bin/python ]; then
  python3 -m venv /opt/nas-monitor/.venv
fi
/opt/nas-monitor/.venv/bin/pip install --disable-pip-version-check -r /opt/nas-monitor/requirements.txt

install -m 0644 "$script_dir/nas-monitor.service" /etc/systemd/system/nas-monitor.service
install -m 0755 "$script_dir/nas-monitor" /usr/local/bin/nas-monitor
systemctl daemon-reload

# Stop services from the previous multi-process installation. Their files are
# deliberately left in place so uninstalling this version does not destroy them.
for legacy_service in nas_service cpu_logger cpu_server cpu_temp_logger cpu_temp_server raid_server therm_logger therm_server; do
  systemctl disable --now "$legacy_service.service" 2>/dev/null || true
done
systemctl enable nas-monitor.service
# `enable --now` starts an inactive service but does not restart one that is
# already running. An upgrade must explicitly restart so the process loads the
# newly installed Python files.
systemctl restart nas-monitor.service

attempt=0
while [ "$attempt" -lt 15 ]; do
  if curl --fail --silent http://127.0.0.1:5000/api/v1/health >/dev/null 2>&1; then
    echo "NAS monitor installed successfully: http://$(hostname):5000/"
    exit 0
  fi
  attempt=$((attempt + 1))
  sleep 1
done

echo "Installation completed, but the health check failed." >&2
echo "Run: journalctl -u nas-monitor.service -n 100" >&2
exit 1
