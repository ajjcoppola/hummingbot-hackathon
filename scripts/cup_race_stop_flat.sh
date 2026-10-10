#!/bin/zsh
# Cup race STOP — bootout agents, stop bots, close LP, leave wallet flat. No redeploy.
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:${HOME}/.orbstack/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="${HB_HACKATHON_ROOT:-${HOME}/proj/hummingbot-hackathon}"
cd "$ROOT"
mkdir -p data/cup_race_autotimer
LOG="data/cup_race_autotimer/stop.log"
exec >>"$LOG" 2>&1
echo "==== cup_race_stop_flat $(date -u +%Y-%m-%dT%H:%M:%SZ) ===="

UID_NUM="$(id -u)"
launchctl bootout "gui/${UID_NUM}/com.hummingbot.mainnet-watchdog" 2>/dev/null || true
launchctl bootout "gui/${UID_NUM}/com.hummingbot.mainnet-reporter" 2>/dev/null || true
echo "LaunchAgents booted out"

python3 - <<'PY'
"""Stop bots, close any LP, no redeploy."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path.cwd()))

from scripts.mainnet_lib import (  # noqa: E402
    ApiClient,
    MAINNET_NETWORK,
    MAINNET_POOL,
    MAINNET_PREFIX,
    DEFAULT_WALLET,
    bot_status,
    close_position,
    docker_rm_force,
    matching_bots,
    portfolio_state,
    positions_owned,
    stop_bot,
    utc_now,
)

client = ApiClient()
log: dict = {"ts": utc_now(), "mode": "cup_stop_flat", "steps": []}

bots = matching_bots(bot_status(client), MAINNET_PREFIX)
names = list(bots.keys())
for name in names:
    try:
        stop_bot(client, name)
        log["steps"].append({"stop": name, "ok": True})
    except Exception as e:
        log["steps"].append({"stop": name, "ok": False, "error": str(e)})
    time.sleep(1)
errs = docker_rm_force(names)
log["steps"].append({"docker_rm": names, "errors": errs})

pos = positions_owned(client, network=MAINNET_NETWORK, pool=MAINNET_POOL, wallet=DEFAULT_WALLET)
log["positions_before"] = [p.get("position_address") for p in pos]

if not pos:
    log["ok"] = True
    log["detail"] = "already flat (no LP)"
    print(json.dumps(log, indent=2, default=str))
    raise SystemExit(0)

addr = pos[0].get("position_address")
try:
    close_resp = close_position(
        client,
        network=MAINNET_NETWORK,
        position_address=addr,
        wallet=DEFAULT_WALLET,
        pool=MAINNET_POOL,
        slippage_pct=3.0,
    )
    log["steps"].append({"close": close_resp})
except Exception as e:
    # R003m/S001: Gateway may 400 while close lands on-chain
    log["steps"].append({"close_error": str(e)})

deadline = time.time() + 300
flat = False
while time.time() < deadline:
    pos2 = positions_owned(client, network=MAINNET_NETWORK, pool=MAINNET_POOL, wallet=DEFAULT_WALLET)
    addrs = {p.get("position_address") for p in pos2}
    if not pos2 or addr not in addrs:
        flat = True
        break
    # also treat position-info gone as flat
    time.sleep(3)

ps = portfolio_state(client)
main = ((ps or {}).get("master_account") or {}).get("solana-mainnet-beta") or []
log["portfolio_api"] = {r.get("token"): r.get("available_units") for r in main}
log["flat"] = flat
log["ok"] = flat
print(json.dumps(log, indent=2, default=str))
raise SystemExit(0 if flat else 1)
PY

echo "STOP_OK $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee data/cup_race_autotimer/stopped_at.txt
