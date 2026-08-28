# Pi Zero 2W display-agent hardware test

The supported deployment path runs from the Pi 5 over SSH on the USB gadget
network. The Zero does not need Wi-Fi, DNS, GitHub, PyPI, or a default internet
route. It needs SSH enabled and the `nas` account reachable at `10.99.0.2`.

After pulling this branch, upgrade the Pi 5 installation once so it has the
display source and deployment command:

```bash
cd ~/RaspberryPi_NAS
git pull --ff-only
sudo ./install/pi5/install-pi5.sh
nas-monitor deploy-display
```

The command downloads/builds the Python wheels on the Pi 5, packages the Zero
application, copies it with SCP, and runs the offline installer through SSH. It
prompts for the Zero account and sudo credentials without storing them.

Custom SSH account or gadget address:

```bash
nas-monitor deploy-display --user nas --host 10.99.0.2
```

## Direct development installation

The Zero agent uses `10.99.0.1` by default in gadget mode. Direct installation
on the Zero remains available for development, but requires temporary internet
access to download packages:

```bash
cd ~/RaspberryPi_NAS
git pull --ff-only
sudo ./install/zero/install-zero.sh
```

To intentionally use the Wi-Fi escape hatch, pass the Pi 5's LAN address
explicitly. This overrides the gadget-mode default:

```bash
sudo ./install/zero/install-zero.sh --server 192.168.1.50
```

Every installation updates the server address in the existing configuration;
the remaining display settings and cached state are preserved.

The installer removes only the legacy `/home/nas/display/display.sh` cron entry,
then installs and restarts one `nas-display.service`.

Verify connectivity and service state:

```bash
nas-display doctor
nas-display status
nas-display logs
```

The first successful run refreshes the display. Later polling does not refresh
the panel until the configured interval is due, the screen or policy changes,
an alert changes state, or connectivity changes between online and offline.
Identical rendered images are skipped.

Normal uninstall preserves the server configuration and cached state:

```bash
nas-display uninstall
```

Complete removal is explicit:

```bash
nas-display uninstall --purge
```
