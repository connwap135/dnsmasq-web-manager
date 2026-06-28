# Dnsmasq Web Manager — Agent Instructions

## Project Overview

Flask-based web UI for managing dnsmasq DNS host mappings. Single-file backend (`app.py`), single-page frontend (`templates/index.html`), systemd services for deployment.

## ⛔ Critical Constraints

**NEVER modify any services or DNS configuration on the local development machine (this workstation).** This includes but is not limited to:
- `systemctl` commands (start/stop/restart/enable/disable/mask)
- `resolv.conf`, `systemd-resolved`, NetworkManager DNS settings
- Any `nmcli`, `resolvectl`, or `dnsmasq` operations on localhost
- All service/DNS changes must be scoped to the remote server **192.168.3.32** only

## Architecture

```
Browser → Flask (app.py, port 8080) → /etc/dnsmasq.hosts → dnsmasq (:53) → upstream DNS
```

- **Backend**: `app.py` — Flask single-file app, reads/writes `/etc/dnsmasq.hosts` via atomic write (`tempfile` + `os.replace`)
- **Frontend**: `templates/index.html` — Pure HTML/CSS/JS, dark theme, no CDN dependencies
- **Config**: `config/dnsmasq.conf` — dnsmasq global config with `neg-ttl=0`, `clear-on-reload`, upstream includes gateway `192.168.0.1`
- **Services**: `systemd/dnsmasq-web.service` (Flask app), `systemd/fix-resolv.service` (ensures resolv.conf → 127.0.0.1)
- **Scripts**: `scripts/install.sh` (one-click deploy), `scripts/uninstall.sh` (cleanup)

## Server Info

- **Target server**: `192.168.3.32` (SSH: `root@192.168.3.32`)
- **OS**: Ubuntu 24.04.4 LTS
- **dnsmasq version**: 2.90
- **Web UI**: `http://192.168.3.32:8080`

## Development

### Run locally (development)
```bash
python3 app.py  # http://localhost:8080
```

### Deploy to server
```bash
# Copy files to server
sshpass -p '...' scp app.py root@192.168.3.32:/opt/dnsmasq-web/
sshpass -p '...' scp config/dnsmasq.conf root@192.168.3.32:/etc/dnsmasq.conf

# Restart services on server (NOT locally)
sshpass -p '...' ssh root@192.168.3.32 "systemctl restart dnsmasq dnsmasq-web"
```

## Key Conventions

- **Atomic file writes**: Always use `tempfile` + `os.replace` pattern when writing to `/etc/dnsmasq.hosts` — dnsmasq uses inotify and will read a truncated file during non-atomic writes
- **Service reload**: `reload_dnsmasq()` tries `systemctl reload` first (SIGHUP), falls back to `restart` only if reload fails
- **Input validation**: IPv4 regex + RFC hostname validation on all web routes; API routes should also validate (currently missing — see known issues)
- **No external dependencies**: Frontend is pure HTML/CSS/JS, no npm/CDN. Backend only requires Flask.

## File Roles

| File | Purpose |
|------|---------|
| `app.py` | Flask backend — all routes, validation, hosts file I/O |
| `templates/index.html` | Single-page UI with dark theme |
| `config/dnsmasq.conf` | dnsmasq configuration (deployed to `/etc/dnsmasq.conf`) |
| `config/fix-resolv-conf.sh` | Ensures resolv.conf points to 127.0.0.1 |
| `systemd/dnsmasq-web.service` | systemd unit for Flask app |
| `systemd/fix-resolv.service` | systemd unit to fix resolv.conf on boot |
| `scripts/install.sh` | One-click server deployment |
| `scripts/uninstall.sh` | Cleanup and remove services |
| `docs/deployment.md` | Deployment guide and architecture |

## Known Issues

- API `POST /api/hosts` does not validate hostname format (web routes do)
- No `requirements.txt` — Flask version not locked
- No authentication — anyone on the network can manage DNS
- `secret_key` regenerates on every restart, invalidating sessions
- `write_hosts()` was recently fixed to use atomic write (commit `7d09a22`)
