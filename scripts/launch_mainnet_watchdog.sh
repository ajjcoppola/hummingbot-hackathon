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
RUN_ID="${WATCHDOG_REPORTER_RUN_ID:-R003m_mainnet_100_w16_20260928}"
THRESHOLD="${WATCHDOG_THRESHOLD_PCT:-0.5}"
# Anti-flake defaults (R003m 2026-09-29): sticky LP probe + confirmed-flat before
# hard-restart; Gateway restart only while LP visible + 30m cooldown.
exec /usr/bin/env PYTHONUNBUFFERED=1 /opt/homebrew/bin/python3 -u \
  research/mainnet_health_watchdog.py \
  --reporter-run-id "$RUN_ID" \
  --rebalance-threshold-pct "$THRESHOLD" \
  --interval 120 \
  --flat-polls 8 \
  --flat-restart-cooldown-s 3600 \
  --info-fail-limit 8 \
  --gateway-restart-cooldown-s 1800 \
  --pos-retries 3 \
  --pos-retry-delay-s 2.0 \
  --min-free-usdc-flat 40 \
  >> data/mainnet_watchdog/watchdog.log 2>&1
