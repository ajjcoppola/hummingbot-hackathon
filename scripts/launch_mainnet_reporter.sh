#!/bin/zsh
# Supervised entrypoint for mainnet endurance reporter (LaunchAgent KeepAlive).
# Do not start the reporter from Cursor agent shells — use this or launchctl.
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:${HOME}/.orbstack/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="${HOME}/proj/hummingbot-hackathon"
cd "$ROOT"
mkdir -p data/devnet_runs
RUN_ID="${REPORTER_RUN_ID:-T015_mainnet_100_hb217_20260927}"
WIDTH="${REPORTER_WIDTH:-1.0}"
THRESHOLD="${REPORTER_THRESHOLD_PCT:-0.05}"
QUOTE="${REPORTER_TOTAL_AMOUNT_QUOTE:-100}"
exec /usr/bin/env PYTHONUNBUFFERED=1 /opt/homebrew/bin/python3 -u \
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
