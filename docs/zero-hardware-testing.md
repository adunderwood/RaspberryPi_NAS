# Pi Zero 2W display-agent hardware test

The Zero agent uses `10.99.0.1` by default in gadget mode. The only normal local
configuration is the Pi 5 hostname or IP address.

```bash
cd ~/RaspberryPi_NAS
git pull --ff-only
sudo ./install/zero/install-zero.sh
```

For Wi-Fi instead of gadget mode:

```bash
sudo ./install/zero/install-zero.sh --server nas.local
```

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
