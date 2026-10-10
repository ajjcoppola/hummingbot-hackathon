#!/bin/zsh
# Wait for Botcamp Cup start → deploy race → wait until +48h → flatten.
# Start/end from botcamp.xyz page (2026-10-07T02:00Z → 2026-10-09T02:00Z).
# Requires Amphetamine (or equivalent) so Mac sleep does not pause this timer.
set -euo pipefail
export PATH="/usr/local/bin:/opt/homebrew/bin:${HOME}/.orbstack/bin:/usr/bin:/bin:/usr/sbin:/sbin"

ROOT="${HB_HACKATHON_ROOT:-${HOME}/proj/hummingbot-hackathon}"
cd "$ROOT"
mkdir -p data/cup_race_autotimer
STATE="data/cup_race_autotimer/state.json"
LOG="data/cup_race_autotimer/autotimer.log"

# Official Cup window (UTC) scraped from botcamp leaderboard countdown target
RACE_START_UTC="${CUP_RACE_START_UTC:-2026-10-07T02:00:00Z}"
RACE_END_UTC="${CUP_RACE_END_UTC:-2026-10-09T02:00:00Z}"

log() { echo "[$(date -u +%Y-%m-%dT%H:%M:%SZ)] $*" | tee -a "$LOG"; }

write_state() {
  local phase="$1"
  python3 - "$STATE" "$phase" "$RACE_START_UTC" "$RACE_END_UTC" <<'PY'
import json, sys
from datetime import datetime, timezone
path, phase, start, end = sys.argv[1:5]
row = {
  "phase": phase,
  "race_start_utc": start,
  "race_end_utc": end,
  "updated": datetime.now(timezone.utc).isoformat(),
}
with open(path, "w") as f:
  json.dump(row, f, indent=2)
  f.write("\n")
PY
}

epoch_of() {
  # macOS date: -j -f
  date -j -u -f "%Y-%m-%dT%H:%M:%SZ" "$1" "+%s" 2>/dev/null \
    || date -u -d "$1" "+%s"
}

START_S="$(epoch_of "$RACE_START_UTC")"
END_S="$(epoch_of "$RACE_END_UTC")"
NOW_S="$(date -u +%s)"

log "autotimer boot start=$RACE_START_UTC end=$RACE_END_UTC now=$(date -u +%Y-%m-%dT%H:%M:%SZ)"

# Already finished?
if [[ -f data/cup_race_autotimer/stopped_at.txt ]] && [[ "$NOW_S" -ge "$END_S" ]]; then
  log "already stopped after end — exit"
  write_state "done"
  exit 0
fi

# Wait for start
if [[ "$NOW_S" -lt "$START_S" ]]; then
  WAIT=$((START_S - NOW_S))
  log "waiting ${WAIT}s until race start"
  write_state "waiting_start"
  sleep "$WAIT"
else
  log "past start — proceeding"
fi

# Start (idempotent)
if [[ ! -f data/cup_race_autotimer/started_at.txt ]]; then
  write_state "starting"
  log "invoking cup_race_start.sh"
  /bin/zsh "$ROOT/scripts/cup_race_start.sh" || {
    log "START FAILED — see data/cup_race_autotimer/start.log"
    write_state "start_failed"
    exit 1
  }
else
  log "started_at.txt exists — skip start script"
fi
write_state "running"

# Wait for end
NOW_S="$(date -u +%s)"
if [[ "$NOW_S" -lt "$END_S" ]]; then
  WAIT=$((END_S - NOW_S))
  log "racing; sleeping ${WAIT}s until end"
  sleep "$WAIT"
fi

# Stop
write_state "stopping"
log "invoking cup_race_stop_flat.sh"
/bin/zsh "$ROOT/scripts/cup_race_stop_flat.sh" || {
  log "STOP reported non-zero — check stop.log / on-chain (close may still have landed)"
  write_state "stop_uncertain"
  exit 1
}
write_state "done"
log "autotimer complete"
exit 0
