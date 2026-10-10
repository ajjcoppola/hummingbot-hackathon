#!/usr/bin/env bash
# Copy Mac Hummingbot API + hackathon repo to Hermes over SSH.
# Usage:
#   export HERMES_HOST=user@droplet
#   ./scripts/hermes/rsync_from_mac.sh [--dry-run]
# See docs/HERMES_COPY_MIGRATE.md. Never commit secrets; this transfers .env over SSH only.
set -euo pipefail

DRY=()
if [[ "${1:-}" == "--dry-run" ]]; then
  DRY=(--dry-run)
  shift
fi

HERMES_HOST="${HERMES_HOST:?Set HERMES_HOST=user@host}"
HERMES_API_DIR="${HERMES_API_DIR:-/opt/hummingbot-v216/hummingbot-api}"
HERMES_HACKATHON_DIR="${HERMES_HACKATHON_DIR:-/opt/hummingbot-hackathon}"
MAC_API_DIR="${MAC_API_DIR:-${HOME}/proj/hummingbot-v216/hummingbot-api}"
MAC_HACKATHON_DIR="${MAC_HACKATHON_DIR:-${HOME}/proj/hummingbot-hackathon}"
RSYNC_SSH="${RSYNC_SSH:-ssh}"

if [[ ! -d "$MAC_API_DIR" ]]; then
  echo "missing MAC_API_DIR=$MAC_API_DIR" >&2
  exit 1
fi
if [[ ! -d "$MAC_HACKATHON_DIR" ]]; then
  echo "missing MAC_HACKATHON_DIR=$MAC_HACKATHON_DIR" >&2
  exit 1
fi

echo "==> ensure remote dirs on $HERMES_HOST"
$RSYNC_SSH "$HERMES_HOST" "mkdir -p '$HERMES_API_DIR' '$HERMES_HACKATHON_DIR' '$(dirname "$HERMES_API_DIR")'"

echo "==> rsync hummingbot-api (incl. .env + gateway-files)"
rsync -azP "${DRY[@]}" \
  -e "$RSYNC_SSH" \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache/' \
  --exclude 'bots/instances/' \
  --exclude 'bots/logs/' \
  "$MAC_API_DIR/" \
  "${HERMES_HOST}:${HERMES_API_DIR}/"

echo "==> rsync hummingbot-hackathon"
rsync -azP "${DRY[@]}" \
  -e "$RSYNC_SSH" \
  --exclude '.git/' \
  --exclude '__pycache__/' \
  --exclude '*.pyc' \
  --exclude '.pytest_cache/' \
  --exclude 'data/devnet_runs/' \
  --exclude 'data/mainnet_watchdog/' \
  --exclude 'data/pool_snapshots.jsonl' \
  --exclude 'canvases/' \
  --exclude 'docs/tearsheets/' \
  --exclude 'submission/orca_race_case/pdf/' \
  "$MAC_HACKATHON_DIR/" \
  "${HERMES_HOST}:${HERMES_HACKATHON_DIR}/"

if [[ ${#DRY[@]} -eq 0 ]]; then
  echo "==> remind: edit BOTS_PATH in ${HERMES_API_DIR}/.env to Linux path"
  $RSYNC_SSH "$HERMES_HOST" "grep -n 'BOTS_PATH\|/Users/' '${HERMES_API_DIR}/.env' 2>/dev/null | head -20 || true"
fi

echo "done ${DRY[*]:-}"
echo "Next: docs/HERMES_COPY_MIGRATE.md §3 docker compose up"
