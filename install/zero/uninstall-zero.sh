#!/bin/sh
set -eu
if [ "$(id -u)" -ne 0 ]; then echo "Run this uninstaller with sudo." >&2; exit 1; fi
purge=false
if [ "${1:-}" = "--purge" ]; then purge=true; shift; fi
if [ "$#" -ne 0 ]; then echo "Usage: uninstall-zero.sh [--purge]" >&2; exit 2; fi
systemctl disable --now nas-display.service 2>/dev/null || true
rm -f /etc/systemd/system/nas-display.service
systemctl daemon-reload
if [ "$purge" = true ]; then
  rm -f /usr/local/bin/nas-display
  rm -rf /opt/nas-display /etc/nas-display /var/lib/nas-display
  userdel nas-display 2>/dev/null || true
  echo "NAS display uninstalled and state purged."
else
  find /opt/nas-display -mindepth 1 -maxdepth 1 ! -name uninstall-zero.sh -exec rm -rf -- {} +
  echo "NAS display uninstalled. Preserved configuration and cached state."
  echo "Run 'nas-display uninstall --purge' later to remove all preserved data."
fi
