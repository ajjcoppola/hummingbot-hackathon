# Mainnet ops — restart, health, reporter

zsh-safe **one-liners**. Do not paste multi-line JSON curls.

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
# Stop bots, keep LP, skip deploy-open
python3 scripts/mainnet_bot_ops.py adopt
# Close that LP then clean managed OPEN
python3 scripts/mainnet_bot_ops.py adopt --recycle --restart-gateway

# Reporter (threshold must match live YAML — currently 0.05)
python3 scripts/mainnet_bot_ops.py restart-reporter --run-id T013_mainnet_100_width1_20260925 --threshold 0.05
```

## Health watchdog (leave running)

```bash
PYTHONUNBUFFERED=1 python3 -u research/mainnet_health_watchdog.py \
  --reporter-run-id T013_mainnet_100_width1_20260925 \
  --interval 120 \
  >> data/mainnet_watchdog/watchdog.log 2>&1 &
```

Behavior:

| Condition | Action |
|-----------|--------|
| `position_info` fails N times | Restart Gateway |
| Mild OOR (spot still inside limit hysteresis) | Soft-restart bot (cooldown) |
| Spot **past** auto-close limits for N polls | **`adopt --recycle`** (close orphan + redeploy) |
| Reporter snapshots stale | `restart-reporter` |
| Multiple bots / orphan LP | **Alert only** (or recycle if past-limit path) |

Never auto-deploys Devnet. Never opens a second LP without closing the first.

## Stuck OOR past limit (root cause)

Auto-close **does** fire when spot crosses limit prices. If Gateway `clmm/close` returns `SIMULATION_FAILED` (non-retryable), the executor dies `FAILED` while the LP stays on-chain. Official `lp_rebalancer` then **halts** (“position still open… recover manually”). Soft-restart clears the halt and tries a **second OPEN** → `INSUFFICIENT_BALANCE`. Capital looks “stuck OOR” for hours even though limits were breached.

**Fix:** Gateway close + clean redeploy (`adopt --recycle`). Watchdog now does this automatically after `--past-limit-polls` (default 2).

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
python3 scripts/mainnet_bot_ops.py adopt --recycle --restart-gateway
python3 scripts/mainnet_bot_ops.py restart-reporter --run-id T013_mainnet_100_width1_20260925 --threshold 0.05
```

If still stuck HOLD with `position_info` FAIL and no LP:

```bash
python3 scripts/mainnet_bot_ops.py hard-restart --restart-gateway
python3 scripts/mainnet_bot_ops.py restart-reporter --run-id T013_mainnet_100_width1_20260925 --threshold 0.05
```

**Why `adopt` (not hard-restart with open LP):** official `lp_rebalancer` does not attach an orphan on-chain position into a new executor. Redeploying while an LP exists tries a second OPEN, fails (insufficient free USDC), and spams `CloseType.FAILED`.
