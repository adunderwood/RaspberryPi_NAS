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
rm -f /etc/systemd/system/nas-monitor.service
systemctl daemon-reload

if [ "$purge" = true ]; then
  rm -f /usr/local/bin/nas-monitor
  rm -rf /opt/nas-monitor
  rm -rf /etc/nas-monitor /var/lib/nas-monitor
  userdel nas-monitor 2>/dev/null || true
  echo "NAS monitor uninstalled and configuration/database purged."
else
  # Keep only the uninstaller and its small command wrapper so a later
  # `nas-monitor uninstall --purge` remains available.
  find /opt/nas-monitor -mindepth 1 -maxdepth 1 ! -name uninstall-pi5.sh -exec rm -rf -- {} +
  echo "NAS monitor uninstalled. Preserved configuration and database."
  echo "Run 'nas-monitor uninstall --purge' later to remove all preserved data."
fi
