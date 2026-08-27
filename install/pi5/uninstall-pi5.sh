#!/bin/sh
set -eu

if [ "$(id -u)" -ne 0 ]; then
  echo "Run this uninstaller with sudo." >&2
  exit 1
fi

purge=false
if [ "${1:-}" = "--purge" ]; then purge=true; fi
if [ "$#" -gt 0 ] && [ "${1:-}" != "--purge" ]; then
  echo "Usage: uninstall-pi5.sh [--purge]" >&2
  exit 2
fi

systemctl disable --now nas-monitor.service 2>/dev/null || true
rm -f /etc/systemd/system/nas-monitor.service /usr/local/bin/nas-monitor
systemctl daemon-reload
rm -rf /opt/nas-monitor

if [ "$purge" = true ]; then
  rm -rf /etc/nas-monitor /var/lib/nas-monitor
  userdel nas-monitor 2>/dev/null || true
  echo "NAS monitor uninstalled and configuration/database purged."
else
  echo "NAS monitor uninstalled. Preserved /etc/nas-monitor and /var/lib/nas-monitor."
fi
