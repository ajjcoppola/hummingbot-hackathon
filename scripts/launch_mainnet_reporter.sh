#!/bin/zsh
# Supervised entrypoint for mainnet endurance reporter (LaunchAgent / systemd KeepAlive).
# Do not start the reporter from Cursor agent shells — use launchctl or systemd.
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:${HOME}/.orbstack/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="${HB_HACKATHON_ROOT:-${HOME}/proj/hummingbot-hackathon}"
cd "$ROOT"
mkdir -p data/devnet_runs
RUN_ID="${REPORTER_RUN_ID:-S001_mainnet_120_w16_20261006}"
WIDTH="${REPORTER_WIDTH:-16.0}"
THRESHOLD="${REPORTER_THRESHOLD_PCT:-0.5}"
QUOTE="${REPORTER_TOTAL_AMOUNT_QUOTE:-120}"
if [[ -x /opt/homebrew/bin/python3 ]]; then
  PY=/opt/homebrew/bin/python3
elif [[ -x /usr/local/bin/python3 ]]; then
  PY=/usr/local/bin/python3
else
  PY="$(command -v python3)"
fi
exec /usr/bin/env PYTHONUNBUFFERED=1 "$PY" -u \
  research/devnet_run_reporter.py \
  --run-id "$RUN_ID" \
  --network solana-mainnet-beta \
  --quote-token USDC \
  --pool Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE \
  --wallet 2ZuShDjgEkdiTtEqbSSCzGUhh5kaFqMjhiuC2VPUNXoB \
  --bot-filter orca_tight_mainnet_smoke \
  --width "$WIDTH" \
  --threshold "$THRESHOLD" \
  --total-amount-quote "$QUOTE" \
  --interval 120 \
  >> "data/devnet_runs/${RUN_ID}.reporter.log" 2>&1
