#!/bin/sh
set -eu

host=10.99.0.2
user=nas
while [ "$#" -gt 0 ]; do
  case "$1" in
    --host) [ -n "${2:-}" ] || { echo "--host requires a value" >&2; exit 2; }; host=$2; shift 2 ;;
    --user) [ -n "${2:-}" ] || { echo "--user requires a value" >&2; exit 2; }; user=$2; shift 2 ;;
    *) echo "Usage: deploy-zero.sh [--host HOST] [--user USER]" >&2; exit 2 ;;
  esac
done

source_dir=/opt/nas-monitor/display-source
[ -d "$source_dir/Raspberry Pi Zero 2w/nas_display" ] || {
  echo "Display deployment source is missing. Re-run the Pi 5 installer." >&2
  exit 1
}
for command_name in ssh scp tar mktemp; do
  command -v "$command_name" >/dev/null || { echo "$command_name is required" >&2; exit 1; }
done

work_dir=$(mktemp -d)
control_socket="$work_dir/ssh-control"
remote_archive="/tmp/nas-display-bundle-$$.tar.gz"
remote_dir="/tmp/nas-display-bundle-$$"
connection_open=false
cleanup() {
  if [ "$connection_open" = true ]; then
    ssh -o ControlPath="$control_socket" -O exit "$user@$host" >/dev/null 2>&1 || true
  fi
  rm -rf "$work_dir"
}
trap cleanup EXIT INT TERM

bundle="$work_dir/bundle"
wheelhouse="$bundle/wheelhouse"
mkdir -p "$bundle/Raspberry Pi Zero 2w" "$bundle/config" "$bundle/install/zero" "$wheelhouse"
cp -a "$source_dir/Raspberry Pi Zero 2w/nas_display" "$bundle/Raspberry Pi Zero 2w/"
cp "$source_dir/Raspberry Pi Zero 2w/nas.py" "$source_dir/Raspberry Pi Zero 2w/requirements.txt" \
  "$bundle/Raspberry Pi Zero 2w/"
cp "$source_dir/config/zero.example.toml" "$bundle/config/"
cp "$source_dir/install/zero/"* "$bundle/install/zero/"

echo "Preparing offline Python packages for the Pi Zero 2W..."
/opt/nas-monitor/.venv/bin/pip wheel --disable-pip-version-check \
  --wheel-dir "$wheelhouse" -r "$source_dir/Raspberry Pi Zero 2w/requirements.txt"
tar -C "$work_dir" -czf "$work_dir/nas-display-bundle.tar.gz" bundle

echo "Connecting to $user@$host over the USB gadget network..."
ssh -M -S "$control_socket" -o ControlPersist=60 -fN "$user@$host"
connection_open=true
scp -o ControlPath="$control_socket" "$work_dir/nas-display-bundle.tar.gz" "$user@$host:$remote_archive"

echo "Installing the display agent on the Pi Zero 2W..."
ssh -t -o ControlPath="$control_socket" "$user@$host" \
  "set -eu; mkdir '$remote_dir'; tar -xzf '$remote_archive' -C '$remote_dir'; sudo '$remote_dir/bundle/install/zero/install-zero.sh' --server 10.99.0.1 --wheelhouse '$remote_dir/bundle/wheelhouse'; rm -rf '$remote_dir' '$remote_archive'; nas-display doctor"

echo "Pi Zero 2W display deployment completed successfully."
