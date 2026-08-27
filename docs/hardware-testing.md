# Public feature-branch hardware testing

Hardware changes are developed on a public feature branch before they are merged
into `main`. Never commit `.env` files, private keys, tokens, host inventories,
database files, or copied production configuration.

## First Pi 5 test

On the Pi 5, clone the repository if it is not already present:

```bash
git clone --branch codex/pi5-foundation https://github.com/adunderwood/RaspberryPi_NAS.git
cd RaspberryPi_NAS
sudo ./install/pi5/install-pi5.sh
```

For a later build on the same branch:

```bash
git fetch origin
git switch codex/pi5-foundation
git pull --ff-only
sudo ./install/pi5/install-pi5.sh
```

The installer is also the upgrader. It preserves `/etc/nas-monitor/config.toml`
and `/var/lib/nas-monitor/metrics.sqlite3`, replaces application-owned files,
updates the virtual environment, restarts the service, and performs a health
check.

## Verification

```bash
nas-monitor doctor
curl http://127.0.0.1:5000/api/v1/snapshot
curl http://10.99.0.1:5000/cpu
```

The final command checks compatibility with the currently deployed Zero client.
For diagnostics:

```bash
nas-monitor status
nas-monitor logs
```

## Uninstall

```bash
nas-monitor uninstall
```

This preserves configuration and the SQLite database. To remove those too:

```bash
nas-monitor uninstall --purge
```

The small uninstall command remains installed after a normal uninstall, allowing
the preserved configuration and database to be purged later.

The installer disables the old service units to prevent port conflicts but does
not delete their files. This makes the first migration reversible if hardware
testing uncovers a problem.
