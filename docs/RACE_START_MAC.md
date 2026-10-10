# Cup race start — Mac (primary)

Host decision: [`RACE_HOST.md`](RACE_HOST.md). Wallet should be **flat** before this (no open LP). Live YAML: `configs/lp_rebalancer_s001_120.yml` → API `orca_tight_mainnet_smoke` (16% / 0.5 / quote 120).

Images: `hummingbot/hummingbot:version-2.17.0`, `hummingbot/gateway:version-2.17.0`. Condor optional; **do not** let `/agent` place or cancel LP.

## Botcamp window (from leaderboard)

| | UTC | PT (America/Los_Angeles) |
|--|-----|---------------------------|
| **Start** | `2026-10-07T02:00:00Z` | 2026-10-06 **19:00** |
| **End** (+48h) | `2026-10-09T02:00:00Z` | 2026-10-08 **19:00** |

Source: [botcamp leaderboard](https://www.botcamp.xyz/hackathons/agent-builders-cup-1#leaderboard) countdown targets.

## Autotimer (preferred)

Auto-start at Cup open and flatten at +48h via LaunchAgent:

```bash
cd ~/proj/hummingbot-hackathon
# Amphetamine → indefinite FIRST (sleep pauses the waiter)
cp scripts/com.hummingbot.cup-race-autotimer.plist ~/Library/LaunchAgents/
launchctl bootout gui/$(id -u)/com.hummingbot.cup-race-autotimer 2>/dev/null || true
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hummingbot.cup-race-autotimer.plist
tail -f data/cup_race_autotimer/autotimer.log
```

State: `data/cup_race_autotimer/state.json`. Manual overrides: `scripts/cup_race_start.sh` / `scripts/cup_race_stop_flat.sh`.

## T−15 min checklist

1. Power + lid: plug in; **Amphetamine → indefinite** (prevent sleep).
2. Docker Desktop / OrbStack running (`docker info` works).
3. Confirm flat + Gateway up:

```bash
cd ~/proj/hummingbot-hackathon
python3 scripts/mainnet_bot_ops.py status
```

Expect: `gateway: PASS`, `bots: {}`, `positions: []`, on-chain ~0.6 SOL + ~87 USDC (API portfolio can lag — trust explorer/on-chain if unsure).

4. Sync controller YAML:

```bash
cp configs/lp_rebalancer_s001_120.yml \
  ~/proj/hummingbot-v216/hummingbot-api/bots/conf/controllers/orca_tight_mainnet_smoke.yml
```

5. Confirm Helius / RPC still configured in Gateway `bots/gateway-files` (paid tier preferred for 48h).

## Start race (deploy)

```bash
cd ~/proj/hummingbot-hackathon
python3 scripts/mainnet_bot_ops.py --wait-s 300 hard-restart --restart-gateway
python3 scripts/mainnet_bot_ops.py status
```

Expect: `ok: true`, one running bot, one **in-range** LP.

## Bootstrap LaunchAgents (required)

Do **not** start watchdog/reporter from Cursor (`python … &`).

```bash
cd ~/proj/hummingbot-hackathon
cp scripts/com.hummingbot.mainnet-watchdog.plist ~/Library/LaunchAgents/
cp scripts/com.hummingbot.mainnet-reporter.plist ~/Library/LaunchAgents/
launchctl bootout gui/$(id -u)/com.hummingbot.mainnet-watchdog 2>/dev/null || true
launchctl bootout gui/$(id -u)/com.hummingbot.mainnet-reporter 2>/dev/null || true
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hummingbot.mainnet-watchdog.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hummingbot.mainnet-reporter.plist
```

Verify:

```bash
launchctl print gui/$(id -u)/com.hummingbot.mainnet-watchdog | head -15
launchctl print gui/$(id -u)/com.hummingbot.mainnet-reporter | head -15
sleep 130
tail -1 data/mainnet_watchdog/watchdog.log
tail -2 data/devnet_runs/S001_mainnet_120_w16_20261006.reporter.log
```

## Leave-alone rules

- Cursor may quit; Docker + LaunchAgents keep running.
- Do not soft-restart for mere OOR; recycle only per [`MAINNET_OPS.md`](MAINNET_OPS.md).
- One LP owner only — do not also deploy from Hermes while Mac is racing.
- Ledger: update [`TRIALS_LEDGER.md`](TRIALS_LEDGER.md) START row when you open (bump trial id if needed).

## Emergency flatten

```bash
launchctl bootout gui/$(id -u)/com.hummingbot.mainnet-watchdog 2>/dev/null || true
launchctl bootout gui/$(id -u)/com.hummingbot.mainnet-reporter 2>/dev/null || true
# close LP without redeploy — see MAINNET_OPS / prior stop-flat procedure
python3 scripts/mainnet_bot_ops.py cleanup
# then Gateway close via adopt --recycle path, or status-driven close; confirm on-chain flat
```

Prefer the stop-flat sequence used at S001 STOP (bootout → stop bot → `clmm/close` → verify on-chain SOL/USDC; ignore stale API portfolio).
