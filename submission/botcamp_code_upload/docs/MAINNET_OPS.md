# Mainnet ops — restart, health, reporter

zsh-safe **one-liners**. Do not paste multi-line JSON curls.

**Active trial:** `R003m_mainnet_100_w16_20260928` — Hummingbot + Gateway **`version-2.17.0`**, width **16%**, threshold **0.5**, ~$100 quote (race-shaped; replaces cancelled T016).  
**Race entry YAML:** `configs/lp_rebalancer_race_800.yml` (same band, quote 800).  
**Deferred:** VPS port → [`docs/future-plans/`](future-plans/README.md).  
**IL / pool primer:** [`docs/IL_AND_POOL_DYNAMICS.md`](IL_AND_POOL_DYNAMICS.md).  
**Self-fund $800:** [`docs/UNSANCTIONED_800.md`](UNSANCTIONED_800.md) (do not deploy until wallet funded).

## Cup unattended checklist (Mac)

Before you leave the laptop for multi-day runs:

1. **Amphetamine** set to **indefinite** (prevent sleep). Cursor may quit — Docker + LaunchAgents do not need the IDE.
2. Both LaunchAgents `running`:
   ```bash
   launchctl print gui/$(id -u)/com.hummingbot.mainnet-watchdog | head -15
   launchctl print gui/$(id -u)/com.hummingbot.mainnet-reporter | head -15
   ```
3. Fresh heartbeats (age &lt; 5 min):
   ```bash
   tail -1 data/mainnet_watchdog/watchdog.jsonl
   tail -2 data/devnet_runs/T014_mainnet_100_hb217_20260926.reporter.log
   ```
4. `python3 scripts/mainnet_bot_ops.py status` → `ok: true`, one bot, one in-range LP.
5. Confirm images: `docker ps` shows `hummingbot:version-2.17.0` and `gateway:version-2.17.0`.

Do **not** start watchdog/reporter from Cursor agent shells (`python … &`). Use LaunchAgents only.

## Install / refresh LaunchAgents

```bash
cd ~/proj/hummingbot-hackathon
cp scripts/com.hummingbot.mainnet-watchdog.plist ~/Library/LaunchAgents/
cp scripts/com.hummingbot.mainnet-reporter.plist ~/Library/LaunchAgents/
launchctl bootout gui/$(id -u)/com.hummingbot.mainnet-watchdog 2>/dev/null || true
launchctl bootout gui/$(id -u)/com.hummingbot.mainnet-reporter 2>/dev/null || true
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hummingbot.mainnet-watchdog.plist
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.hummingbot.mainnet-reporter.plist
```

When bumping trial run-id: edit `WATCHDOG_REPORTER_RUN_ID` / `REPORTER_RUN_ID` in both plists (and the defaults in `scripts/launch_mainnet_*.sh`), re-`cp` + re-bootstrap.

## Commands

```bash
cd ~/proj/hummingbot-hackathon

# Validate gateway / bots / portfolio / positions / in_range / position_info
python3 scripts/mainnet_bot_ops.py status

# Stop API bots + docker rm -f all orca_tight_mainnet_smoke*
python3 scripts/mainnet_bot_ops.py cleanup

# Soft-restart the single running bot (keeps open LP) — only for position_info flake / MQTT stuck
# (NOT a rebalance tool; OOR alone does not mean restart)
python3 scripts/mainnet_bot_ops.py soft-restart

# Full recycle when FLAT: cleanup → optional gateway → redeploy → wait for in-range
python3 scripts/mainnet_bot_ops.py hard-restart --restart-gateway

# When 1 LP already exists (do NOT hard-restart — that causes FAILED open spam):
python3 scripts/mainnet_bot_ops.py adopt
# Close that LP then clean managed OPEN (pins HB/Gateway 2.17 via mainnet_lib)
python3 scripts/mainnet_bot_ops.py --wait-s 300 adopt --recycle --restart-gateway
```

Image pins (override with env): `HB_BOT_IMAGE=hummingbot/hummingbot:version-2.17.0`, `HB_GATEWAY_IMAGE=hummingbot/gateway:version-2.17.0`.

## Strategy change mid-trial (safe path)

YAML alone does **not** retarget an open LP. To change width / threshold / size:

```bash
# 1) Edit repo YAML
$EDITOR configs/lp_rebalancer_mainnet_smoke.yml
# 2) Sync to API conf the bot actually loads
cp configs/lp_rebalancer_mainnet_smoke.yml \
  ~/proj/hummingbot-v216/hummingbot-api/bots/conf/controllers/orca_tight_mainnet_smoke.yml
# 3) Close + reopen under new params (pause LaunchAgents first if you want a quiet cutover)
launchctl bootout gui/$(id -u)/com.hummingbot.mainnet-watchdog 2>/dev/null || true
python3 scripts/mainnet_bot_ops.py --wait-s 300 adopt --recycle --restart-gateway
python3 scripts/mainnet_bot_ops.py status
# 4) New ledger trial id + update plist run-ids + re-bootstrap LaunchAgents
# 5) Never soft-restart expecting a rebalance; never hard-restart with LP open
```

## Health watchdog behavior

| Condition | Action |
|-----------|--------|
| `position_info` fails N times | Restart Gateway |
| Mild OOR (spot still inside limit hysteresis) | Soft-restart bot (cooldown) |
| Spot **past** auto-close limits for N polls | **`adopt --recycle`** |
| **Orphan LP** (bot down, 1 position) | **`adopt --recycle`** (not alert-only — T014 lesson) |
| Recycle fails N times | `alert_recycle_failed` — manual intervene |
| Reporter snapshots stale | `restart-reporter` |
| Multiple bots | **Alert only** |

Never auto-deploys Devnet. Never opens a second LP without closing the first.

## Stuck OOR past limit (root cause)

Auto-close **does** fire when spot crosses limit prices. If Gateway `clmm/close` returns `SIMULATION_FAILED` (non-retryable), the executor dies `FAILED` while the LP stays on-chain. Official `lp_rebalancer` then **halts** (“position still open… recover manually”). Soft-restart clears the halt and tries a **second OPEN** → `INSUFFICIENT_BALANCE`. Capital looks “stuck OOR” for hours even though limits were breached.

**Fix:** Gateway close + clean redeploy (`adopt --recycle`). Watchdog does this after `--past-limit-polls` (default 2).

## OOR vs auto-close (read this first)

Official `lp_rebalancer` does **not** close when price merely exits the band. Auto-close fires when spot breaches **limit prices** = band bounds × `(1 ± rebalance_threshold_pct/100)`.

With `rebalance_threshold_pct: 0.05`, that gap is tiny (close almost as soon as OOR). With the old `0.8`, Condor could show OOR + 0 SOL while the executor correctly **HOLDs** until ~0.8% past the upper/lower bound.

Soft-restart does **not** recenter. Recycle / wait for limit-price close does.

## Suggested recovery when Condor `/lp` shows OOR + 0 SOL

```bash
python3 scripts/mainnet_bot_ops.py status
```

1. If **one running bot** + one LP + `position_info` PASS: **wait**. Spot must pass the limit price (~`upper * 1.0005` with threshold 0.05) before close→open. Soft-restart will not help.
2. Soft-restart **only** if `position_info` FAIL or bot MQTT stuck while LP still exists:

```bash
python3 scripts/mainnet_bot_ops.py soft-restart
# wait ~2 min
python3 scripts/mainnet_bot_ops.py status
```

If bot is FAILED-open-spamming while an LP already exists:

```bash
python3 scripts/mainnet_bot_ops.py adopt
# or put capital back under bot control:
python3 scripts/mainnet_bot_ops.py --wait-s 300 adopt --recycle --restart-gateway
```

If still stuck HOLD with `position_info` FAIL and no LP:

```bash
python3 scripts/mainnet_bot_ops.py hard-restart --restart-gateway
```

**Why `adopt` (not hard-restart with open LP):** official `lp_rebalancer` does not attach an orphan on-chain position into a new executor. Redeploying while an LP exists tries a second OPEN, fails (insufficient free USDC), and spams `CloseType.FAILED`.

## T014 flawless 48h pass table

| Check | Pass |
|-------|------|
| Watchdog jsonl | No gap &gt; 10 min |
| Reporter snaps | No gap &gt; 10 min |
| Capital | Exactly one bot, one LP |
| Past-limit | If breached ≥2 polls → recycle (not stranded hours) |
| Status | `ok: true` on spot checks |
| Images | Bot/Gateway still `version-2.17.0` |
