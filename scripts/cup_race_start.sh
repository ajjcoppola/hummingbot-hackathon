#!/bin/zsh
# Cup race START — Mac. Idempotent: skips if one in-range LP already managed.
# See docs/RACE_START_MAC.md. Do not invoke Condor /agent to trade.
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:${HOME}/.orbstack/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="${HB_HACKATHON_ROOT:-${HOME}/proj/hummingbot-hackathon}"
API_CTRL="${HB_API_CONTROLLER:-${HOME}/proj/hummingbot-v216/hummingbot-api/bots/conf/controllers/orca_tight_mainnet_smoke.yml}"
YAML="${ROOT}/configs/lp_rebalancer_s001_120.yml"
cd "$ROOT"
mkdir -p data/cup_race_autotimer
LOG="data/cup_race_autotimer/start.log"
exec >>"$LOG" 2>&1
echo "==== cup_race_start $(date -u +%Y-%m-%dT%H:%M:%SZ) ===="

if [[ ! -f "$YAML" ]]; then
  echo "missing YAML $YAML" >&2
  exit 1
fi

cp "$YAML" "$API_CTRL"
echo "synced controller → $API_CTRL"

# Already racing?
if python3 scripts/mainnet_bot_ops.py status 2>/dev/null | python3 -c '
import sys, json
d=json.load(sys.stdin)
pos=d.get("positions") or []
bots=d.get("bots") or {}
running=[n for n,s in bots.items() if s=="running"]
ok = len(running)==1 and len(pos)==1 and pos[0].get("in_range") is True
sys.exit(0 if ok else 1)
'; then
  echo "already racing (1 bot + 1 in-range LP) — skip deploy"
else
  echo "hard-restart --restart-gateway"
  python3 scripts/mainnet_bot_ops.py --wait-s 300 hard-restart --restart-gateway
  python3 scripts/mainnet_bot_ops.py status
fi

# LaunchAgents
UID_NUM="$(id -u)"
cp scripts/com.hummingbot.mainnet-watchdog.plist "${HOME}/Library/LaunchAgents/"
cp scripts/com.hummingbot.mainnet-reporter.plist "${HOME}/Library/LaunchAgents/"
launchctl bootout "gui/${UID_NUM}/com.hummingbot.mainnet-watchdog" 2>/dev/null || true
launchctl bootout "gui/${UID_NUM}/com.hummingbot.mainnet-reporter" 2>/dev/null || true
launchctl bootstrap "gui/${UID_NUM}" "${HOME}/Library/LaunchAgents/com.hummingbot.mainnet-watchdog.plist"
launchctl bootstrap "gui/${UID_NUM}" "${HOME}/Library/LaunchAgents/com.hummingbot.mainnet-reporter.plist"
echo "LaunchAgents bootstrapped"
echo "START_OK $(date -u +%Y-%m-%dT%H:%M:%SZ)" | tee data/cup_race_autotimer/started_at.txt
