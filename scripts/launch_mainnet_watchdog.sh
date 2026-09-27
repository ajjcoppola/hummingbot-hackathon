#!/bin/zsh
# Supervised entrypoint for mainnet_health_watchdog (LaunchAgent KeepAlive).
# Do not start the watchdog from Cursor agent shells — use this or launchctl.
set -euo pipefail
# LaunchAgent default PATH omits Docker/OrbStack — soft-restart and recycle need docker.
export PATH="/usr/local/bin:/opt/homebrew/bin:${HOME}/.orbstack/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="${HOME}/proj/hummingbot-hackathon"
cd "$ROOT"
mkdir -p data/mainnet_watchdog
# Current Cup trial — keep in sync with docs/TRIALS_LEDGER.md active run
RUN_ID="${WATCHDOG_REPORTER_RUN_ID:-T015_mainnet_100_hb217_20260927}"
THRESHOLD="${WATCHDOG_THRESHOLD_PCT:-0.05}"
exec /usr/bin/env PYTHONUNBUFFERED=1 /opt/homebrew/bin/python3 -u \
  research/mainnet_health_watchdog.py \
  --reporter-run-id "$RUN_ID" \
  --rebalance-threshold-pct "$THRESHOLD" \
  --interval 120 \
  >> data/mainnet_watchdog/watchdog.log 2>&1
