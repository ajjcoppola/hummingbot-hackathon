# SOL-USDC pool dynamics + impermanent loss (this strat)

Venue: Orca Whirlpool **SOL-USDC** `Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE` (CLMM, ~0.04% fee tier).  
Live path: official `lp_rebalancer` + `LPExecutor` + Gateway. Offline research: `research/orca_backtest_zipline.py`.

## Pool dynamics (concentrated liquidity)

You are **not** in a classic constant-product x·y=k pool. Liquidity only earns fees **inside your tick band**.

| Choice | Upside | Cost |
|--------|--------|------|
| Tight width (e.g. 1%) | High fee density when in-range | High **time out of range** on SOL trends |
| Wide width | More in-range time | Diluted fees per dollar |
| Low `rebalance_threshold_pct` (0.05) | Close almost as soon as OOR | More close→open attempts; gas + failed-close risk |
| High threshold (0.8) | Fewer closes | Can sit OOR earning **zero** fees while Condor shows OOR |

**Inventory flip (concentrated IL):**

- Spot **above** your upper bound → position becomes ~**100% USDC** (pool sold SOL into the rally).
- Spot **below** lower bound → ~**100% SOL**.
- That flip **is** impermanent loss in CLMM form. While OOR you earn **no** fees.

**Rebalance** = close + (autoswap) + open. Cup **Volume** loves it; your wallet pays gas, slippage, rent churn. Failed Gateway close (`SIMULATION_FAILED` / blockhash expiry) can leave an **orphan LP** with the bot dead — fees and volume both stop until `adopt --recycle`.

**Mainnet challenges on this pool:** SOL volatility bursts, priority fees, RPC 429s (Helius free tier), transaction expiry under load, and competing LPs in the same fee stream.

**Race vs self-fund:** Botcamp scores custodian Volume / P&L / Vote on **their** $800. Unsanctioned racing scores **your** MTM after fees, gas, and IL vs a HODL benchmark.

## Impermanent loss primer (for this strat)

**Vanilla IL:** vs holding the starting mix of SOL+USDC, LP value lags when price moves because the pool forces you to sell winners and buy losers.

**Concentrated twist:** outside the band you stop earning and hold a one-sided bag. A SOL rally leaves you USDC-heavy **below** the new spot — you underperform HODL-SOL until you re-enter (buying SOL higher).

| Event | What happens | P&L shape |
|-------|----------------|-----------|
| In-range chop | Earn fee-tier share | Fees can beat small IL |
| Trend through band | OOR; one-sided; no fees | IL + opportunity cost |
| Successful rebal | New band around spot | Realize inventory; pay gas/slip; reset IL clock |
| Failed close / orphan | Stuck OOR one-sided | Worst: IL + zero fees + zero volume |

### Accounting after the competition

1. Every trial row: **money-in**, **HODL benchmark** (start mix or 50/50), **wallet+LP MTM**, **fees**, **gas/rent**, **n_rebals**, **in-range %**, **max orphan minutes**.
2. `edge ≈ LP_book_MTM − HODL_MTM` — do not double-count fees already inside MTM.
3. At **$100**, gas dominates; at **$800**, gas shrinks as % of notional but absolute failed-close risk still matters.
4. Cup P&L ≠ self-fund P&L. Keep Botcamp custodian capital and personal books separate in [`docs/TRIALS_LEDGER.md`](TRIALS_LEDGER.md).

### Ops that make IL survivable

- Watchdog must **recycle orphans**, not only alert ([`research/mainnet_health_watchdog.py`](../research/mainnet_health_watchdog.py)).
- LaunchAgents need a PATH that finds `docker` (OrbStack).
- Strategy changes: edit YAML → `cp` to API conf → `adopt --recycle` (YAML alone does not retarget an open LP).
