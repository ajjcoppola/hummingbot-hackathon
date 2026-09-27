# Unsanctioned $800 racing team (self-fund)

Personal capital on Orca SOL-USDC. **Not** Botcamp custodian $800 — keep books separate.

## Prerequisites

1. P0 watchdog fix live (orphan → `adopt --recycle`; LaunchAgent PATH includes Docker).
2. Wallet `2ZuShDjg…` funded with **≥800 USDC** + **~0.5–1 SOL** gas.
3. Config: [`configs/lp_rebalancer_mainnet_800.yml`](../configs/lp_rebalancer_mainnet_800.yml) (width 1.0 / thr 0.05 until a **real** CSV grid promotes otherwise).
4. Research candidate only: [`configs/lp_rebalancer_mainnet_from_grid.yml`](../configs/lp_rebalancer_mainnet_from_grid.yml) from synthetic grid — **do not** deploy until re-run on real 1m bars.

## Deploy (when funded)

```bash
cd ~/proj/hummingbot-hackathon
# Sync API conf (id must match what deploy uses — either rename to orca_tight_mainnet_smoke
# or extend mainnet_bot_ops --config). Preferred: copy contents into smoke id for one bot:
cp configs/lp_rebalancer_mainnet_800.yml \
  ~/proj/hummingbot-v216/hummingbot-api/bots/conf/controllers/orca_tight_mainnet_smoke.yml
# Ensure total_amount_quote: 800 in that file, then:
python3 scripts/mainnet_bot_ops.py status
# If flat:
python3 scripts/mainnet_bot_ops.py hard-restart --restart-gateway
# If one LP already open at old size:
python3 scripts/mainnet_bot_ops.py --wait-s 420 adopt --recycle --restart-gateway
```

Record a new ledger trial (e.g. T016_800). Update LaunchAgent run-ids.

## Risk / kill switch

| Control | Action |
|---------|--------|
| Kill flatten | `python3 scripts/mainnet_bot_ops.py adopt --recycle` then stop bot / leave flat |
| Daily loss stop | Human: if MTM vs money-in &lt; −X%, flatten and stop LaunchAgents |
| Max orphan | After P0 should be ~0; if `alert_recycle_failed`, intervene manually |
| LLM | Condor `/agent` must **not** place/cancel LP |

## Weekly scorecard (your team)

Fees, IL vs HODL, gas, in-range %, n_rebals, max orphan minutes, bot/Gateway image tags.  
See [`docs/IL_AND_POOL_DYNAMICS.md`](IL_AND_POOL_DYNAMICS.md).

## Compliance

Unsanctioned ≠ invisible. Track lots for tax. No vote-farming claims. Submission copy must not claim Botcamp capital as personal P&L.

## Hermes

Laptop remains the host until you execute [`docs/future-plans/HERMES_WATCHDOG_PORT.md`](future-plans/HERMES_WATCHDOG_PORT.md).
