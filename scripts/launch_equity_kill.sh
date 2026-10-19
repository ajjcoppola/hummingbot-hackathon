#!/bin/zsh
# Supervised entrypoint for scripts/equity_kill.py (LaunchAgent KeepAlive).
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:${HOME}/.orbstack/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="${HB_HACKATHON_ROOT:-${HOME}/proj/hummingbot-hackathon}"
cd "$ROOT"
mkdir -p data/equity_kill
if [[ -x /opt/homebrew/bin/python3 ]]; then
  PY=/opt/homebrew/bin/python3
elif [[ -x /usr/local/bin/python3 ]]; then
  PY=/usr/local/bin/python3
else
  PY="$(command -v python3)"
fi
KILL_PCT="${EQUITY_KILL_PCT:-0.03}"
INTERVAL="${EQUITY_KILL_INTERVAL:-60}"
exec /usr/bin/env PYTHONUNBUFFERED=1 "$PY" -u \
  scripts/equity_kill.py \
  --kill-pct "$KILL_PCT" \
  --interval "$INTERVAL" \
  >> data/equity_kill/launchd.out.log 2>> data/equity_kill/launchd.err.log
