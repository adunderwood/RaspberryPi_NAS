#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then echo "Run this installer with sudo." >&2; exit 1; fi
server=10.99.0.1
if [ "${1:-}" = "--server" ] && [ -n "${2:-}" ]; then server=$2; shift 2; fi
if [ "$#" -ne 0 ]; then echo "Usage: install-zero.sh [--server HOST_OR_IP]" >&2; exit 2; fi

script_dir=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
repo_dir=$(CDPATH= cd -- "$script_dir/../.." && pwd)
app_source="$repo_dir/Raspberry Pi Zero 2w"
command -v python3 >/dev/null || { echo "python3 is required" >&2; exit 1; }
command -v systemctl >/dev/null || { echo "systemd is required" >&2; exit 1; }
command -v curl >/dev/null || { echo "curl is required" >&2; exit 1; }

if ! id nas-display >/dev/null 2>&1; then
  useradd --system --home /var/lib/nas-display --shell /usr/sbin/nologin nas-display
fi
for group in spi gpio i2c; do getent group "$group" >/dev/null && usermod -a -G "$group" nas-display; done
install -d -m 0755 /opt/nas-display /etc/nas-display
install -d -o nas-display -g nas-display -m 0750 /var/lib/nas-display
find /opt/nas-display -mindepth 1 -maxdepth 1 ! -name .venv -exec rm -rf -- {} +
cp -a "$app_source/nas_display" /opt/nas-display/
install -m 0755 "$app_source/nas.py" /opt/nas-display/nas.py
install -m 0644 "$app_source/requirements.txt" /opt/nas-display/requirements.txt
install -m 0755 "$script_dir/uninstall-zero.sh" /opt/nas-display/uninstall-zero.sh

if [ ! -f /etc/nas-display/config.toml ]; then
  sed "s/address = \"10.99.0.1\"/address = \"$server\"/" "$repo_dir/config/zero.example.toml" > /etc/nas-display/config.toml
  chmod 0644 /etc/nas-display/config.toml
fi
if [ ! -x /opt/nas-display/.venv/bin/python ]; then python3 -m venv /opt/nas-display/.venv; fi
/opt/nas-display/.venv/bin/pip install --disable-pip-version-check -r /opt/nas-display/requirements.txt

install -m 0644 "$script_dir/nas-display.service" /etc/systemd/system/nas-display.service
install -m 0755 "$script_dir/nas-display" /usr/local/bin/nas-display

# The legacy display was normally launched by cron. Remove only that exact
# display entry so cron and the long-running agent cannot refresh concurrently.
legacy_user=${SUDO_USER:-nas}
if id "$legacy_user" >/dev/null 2>&1; then
  cron_file=$(mktemp)
  if crontab -u "$legacy_user" -l > "$cron_file" 2>/dev/null; then
    sed -i '\|/home/nas/display/display.sh|d' "$cron_file"
    crontab -u "$legacy_user" "$cron_file"
  fi
  rm -f "$cron_file"
fi
systemctl daemon-reload
systemctl enable nas-display.service
systemctl restart nas-display.service

echo "NAS display installed for server $server."
echo "Run 'nas-display status' and 'nas-display logs' to verify the first refresh."
