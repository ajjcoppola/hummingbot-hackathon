# strategy.md — Orca Tight-Range Leverage Farmer

Required by Agent Builders Cup rule 05 (with complete code and a demo video).

## Intent

Win a **48-hour** scored race (Volume 40% / P&L 40% / HBOT Vote 20%) on **Orca** by maximizing fee capture per dollar of the **$800 USDC** Botcamp account. Long-horizon IL minimization is out of scope.

## Venue

| Item | Value |
|------|--------|
| Team | Orca |
| Protocol | Orca Whirlpools (CLMM) |
| Pair | SOL/USDC |
| Access | Hummingbot Gateway `orca/clmm` on `solana-mainnet-beta` |
| Executor | Hummingbot `lp_executor` |
| Policy | `src/orca_tight_range/logic.py` via `controllers/orca_tight_range_controller.py` |

## Why this is legal for a US person

Self-custodial Solana DEX. No Gate / Bitget / Binance Global / Hyperliquid / Derive account. See `docs/LEGAL_VENUE_GATE.md`.

## Decision loop (unattended)

Every tick:

1. If no position → open a tight band around spot, skewed by 1-minute momentum.
2. If price in band → hold (collect fees, including Orca adaptive fees in vol).
3. If price left the band and deviation ≥ `rebalance_trigger_pct`:
   - **Defer** if the last return is an exhaustion spike (flush).
   - **Hold** if ≥ 6 rebalances already happened in the last hour.
   - Else close and reopen a new tight band.
4. If equity is ≥ 15% below the open mark → halt.

The LLM is not in this loop.

## Parameters

See `configs/orca_tight_range.yml`. Defaults: width 1.5%, skew 0.6, trigger 0.8%, exhaustion 5 min, max 6 reb/hour, stop 15%, capital 800 USDC.

## Intended market conditions

- High SOL/USDC volume (fee velocity)
- Realized vol large enough that a ±1.5% band is visited, not so violent that gas + IL dominate
- Race window only — accept IL on a correct directional lean

## Failure modes we already designed for

| Failure | Guard |
|---------|--------|
| Flush recenter locks IL | Exhaustion filter (`RebalanceDeferred`) |
| Gas death spiral | `max_rebalances_per_hour` |
| Empty `pool_address` | Controller refuses to open |
| Stale 2024 Hummingbot tree | Install plan uses v2.16 Docker, not `~/proj/hummingbot` |
| CEX ToS | Venue gate — Orca only |

## Reproduction

```bash
python3 -m pytest tests/ -q
python3 research/orca_backtest_zipline.py
# then docs/INSTALL_PLAN.md for Gateway
```

## Code freeze

No strategy-logic or parameter edits after **2026-08-31**. Record every pre-freeze trial in `docs/TRIALS_LEDGER.md`.
