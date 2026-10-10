# Hermes copy-migrate (no Condor)

**Backup** off-Mac path. Primary Cup host is Mac — [`RACE_HOST.md`](RACE_HOST.md).

Copy your **existing** Mac Docker/API/Gateway secrets to DigitalOcean droplet [573600155](https://cloud.digitalocean.com/droplets/573600155?i=3d53e4). Do **not** recreate via full Condor `setup.sh`. Do **not** run Condor / Telegram on Hermes for this cutover.

Older rebuild plan (deferred): [`future-plans/HERMES_WATCHDOG_PORT.md`](future-plans/HERMES_WATCHDOG_PORT.md).

## Target layout on Hermes

| Path | Contents |
|------|----------|
| `/opt/hummingbot-v216/hummingbot-api` | Copied compose + `.env` + `bots/` (incl. `gateway-files`) |
| `/opt/hummingbot-hackathon` | This repo (git clone or rsync) |
| systemd | `hummingbot-mainnet-watchdog` + `hummingbot-mainnet-reporter` |

Firewall: **deny public** `:8000` / `:15888`. Bind API/Gateway to localhost; use SSH tunnel or Tailscale from the Mac.

Droplet size: ≥4 GB RAM (8 GB preferred). Race stack ~1.2–1.8 GB steady.

## 1. Prep droplet (console or SSH)

```bash
# On hermes (Ubuntu LTS)
sudo apt-get update
sudo apt-get install -y docker.io docker-compose-v2 git rsync zsh python3 python3-venv curl
sudo usermod -aG docker "$USER"   # re-login after
docker info
sudo mkdir -p /opt/hummingbot-v216 /opt/hummingbot-hackathon
sudo chown -R "$USER:$USER" /opt/hummingbot-v216 /opt/hummingbot-hackathon
```

Install `zsh` — launch scripts are zsh.

## 2. Copy from Mac (run on Mac)

Set host once:

```bash
export HERMES_HOST=root@YOUR_DROPLET_IP   # or user@tailscale-name
# Optional overrides — see scripts/hermes/env.example
```

Dry-run then copy:

```bash
cd ~/proj/hummingbot-hackathon
chmod +x scripts/hermes/rsync_from_mac.sh
./scripts/hermes/rsync_from_mac.sh --dry-run
./scripts/hermes/rsync_from_mac.sh
```

What transfers:

- `hummingbot-api/` compose, `.env`, `bots/` (controllers + **gateway-files** with wallet/Helius)
- `hummingbot-hackathon/` repo (code + configs; excludes huge `data/` caches by default)

**Never** commit `.env` or gateway keys. Transfer only over SSH.

After copy, on Hermes fix Linux paths in `hummingbot-api/.env` if they still say `/Users/ajjc/...` — especially `BOTS_PATH` → `/opt/hummingbot-v216/hummingbot-api/bots`.

## 3. Start API stack on Hermes

```bash
cd /opt/hummingbot-v216/hummingbot-api
docker compose up -d
docker compose ps
# API health (local only)
curl -s -u admin:admin http://127.0.0.1:8000/ | head
```

Start Gateway via API (image pin 2.17):

```bash
curl -s -u admin:admin -X POST http://127.0.0.1:8000/gateway/start \
  -H 'Content-Type: application/json' \
  -d '{"image":"hummingbot/gateway:version-2.17.0","port":15888}'
```

Or from the Mac over SSH tunnel / Tailscale using `scripts/mainnet_bot_ops.py` with `HB_API_URL=http://hermes:8000`.

Sync race YAML:

```bash
cp /opt/hummingbot-hackathon/configs/lp_rebalancer_s001_120.yml \
  /opt/hummingbot-v216/hummingbot-api/bots/conf/controllers/orca_tight_mainnet_smoke.yml
```

## 4. Status while flat

```bash
cd /opt/hummingbot-hackathon
export HB_API_URL=http://127.0.0.1:8000
python3 scripts/mainnet_bot_ops.py status
```

Expect Gateway PASS, no bots, no positions. Confirm wallet `2ZuShDjg…` is the Gateway default (copied gateway-files).

## 5. systemd watchdog + reporter

```bash
cd /opt/hummingbot-hackathon
sudo ./scripts/hermes/install_systemd.sh
sudo systemctl status hummingbot-mainnet-watchdog hummingbot-mainnet-reporter
# After deploy:
journalctl -u hummingbot-mainnet-watchdog -f
```

Units set `HB_HACKATHON_ROOT=/opt/hummingbot-hackathon` and run-id env vars.

**Only enable systemd after** you intend Hermes to own the race. While Mac is primary, leave units **disabled** so two watchdogs never fight.

## 6. Cutover (when Mac stays idle)

1. On Mac: confirm LaunchAgents booted out; no `orca_tight_mainnet_smoke*` container.
2. On Hermes: `python3 scripts/mainnet_bot_ops.py --wait-s 300 hard-restart --restart-gateway`
3. Enable systemd units; confirm watchdog log advances every ~120s for ≥30 min.
4. Ledger: note host=hermes in [`TRIALS_LEDGER.md`](TRIALS_LEDGER.md).

Wallet flat ⇒ no LP migrate. If an LP were open on Mac, stop Mac bot first, copy gateway-files, then `adopt` on Hermes (one owner).

## 7. Rollback to Mac

1. Hermes: `systemctl stop` both units; `python3 scripts/mainnet_bot_ops.py cleanup` (and close LP if any).
2. Mac: start Gateway/API if needed; `hard-restart`; bootstrap LaunchAgents per [`RACE_START_MAC.md`](RACE_START_MAC.md).

## Out of scope

- Condor / Telegram on Hermes
- Cursor Cloud as race host ([`RACE_HOST.md`](RACE_HOST.md))
- Public exposure of API/Gateway ports
