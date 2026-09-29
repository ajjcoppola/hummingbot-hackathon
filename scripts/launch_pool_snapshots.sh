#!/bin/zsh
# Read-only hourly Orca SOL-USDC snapshot collector (ML training data).
# Never touches Gateway / Hummingbot / LP.
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin"
ROOT="${HOME}/proj/hummingbot-hackathon"
cd "$ROOT"
mkdir -p data
exec /usr/bin/env PYTHONUNBUFFERED=1 /opt/homebrew/bin/python3 -u \
  research/pool_snapshot_collector.py \
  --interval 3600 \
  >> data/pool_snapshots_collector.log 2>&1
