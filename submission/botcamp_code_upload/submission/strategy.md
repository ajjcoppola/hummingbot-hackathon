# strategy.md — Orca wide-band SOL/USDC farmer

Required by Agent Builders Cup rule 05 (with complete code and a demo video).

## Intent

Win a **48-hour** scored race (Volume 40% / P&L 40% / HBOT Vote 20%) on **Orca** with Botcamp’s **$800 USDC**. Maximize fees − divergence − gas over the race window. Long-horizon IL minimization is out of scope.

## Venue

| Item | Value |
|------|--------|
| Team | Orca |
| Protocol | Orca Whirlpools (CLMM) |
| Pair | SOL/USDC |
| Pool | `Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE` (0.04%; from Orca API) |
| Access | Hummingbot Gateway `orca/clmm` on `solana-mainnet-beta` |
| Executor | Hummingbot `LPExecutor` via official `lp_rebalancer` |
| Research policy | `src/orca_tight_range/logic.py` + `pool_rank.py` |

## Why this is legal for a US person

Self-custodial Solana DEX. No Gate / Bitget / Binance Global / Hyperliquid / Derive account. See `docs/LEGAL_VENUE_GATE.md`.

## Decision loop (unattended)

Every tick (official `lp_rebalancer`):

1. If no position → open a **16%** full-width RANGE around spot (autoswap to the mix).
2. If price in band → hold (collect fees).
3. If price leaves the band by more than **0.5%** past the edge → close and reopen centered on spot.
4. No hourly rebalance spam: the wide band recenters rarely (R002: tight bands sold the SOL rally).

The LLM is not in this loop. Condor `/agent` must not place or cancel LP.

## Parameters (race)

| Parameter | Value |
|-----------|--------|
| `position_width_pct` | 16.0 |
| `rebalance_threshold_pct` | 0.5 |
| `total_amount_quote` | 800 (race) / 100 (live proof R003m) |
| `autoswap` | true |
| `pool_address` | Czfq3xZZ… (API; never invented) |

## Economic thesis

Tightening a CLMM band scales **fees and loss-versus-rebalancing together** — not a free leverage knob. Offline R002 (Gecko hourly, train 7–21 Sep / holdout 21–28 Sep 2026) reproduced a catastrophic loss for 1.0/0.05 and holdout-promoted **16%/0.5** at 1× share. R003 showed that among **true** SOL-USDC tiers (`tokensBothOf`), only Czfq clears TVL ≥ $500k for an $800 deposit. Botcamp **Volume** = traded volume implied by **fees earned** (not own open/close notional).

## Failure modes

| Failure | Guard |
|---------|--------|
| Flat / dust autoswap loop | Dust floor patch + watchdog flat hard-restart |
| Orphan LP after bot death | Watchdog `adopt --recycle` |
| Empty / invented `pool_address` | Address only from Orca API + ledger |
| API flake mid-race | Prefer single-pool `lp_rebalancer` (no mid-race pool switch required) |
| CEX ToS | Venue gate — Orca only |

## Reproduction

```bash
python3 -m pytest tests/ -q
python3 research/cup_money_search.py          # R002
python3 research/r003_multi_pool_replay.py    # R003
# live: docs/MAINNET_OPS.md + configs/lp_rebalancer_race_800.yml
```

## Live status (honest — see `docs/TRIALS_LEDGER.md`)

**T016** (1.0/0.05) **cancelled** 2026-09-28. Live proof **R003m**: 16%/0.5/~$100 on Czfq. No live P&L claimed without a finished ledger tearsheet.

## Simulation pack (upload with code)

See **`submission/simulations/SIMULATION_RESULTS.md`**.

Hard gate: finish ≥ $800 start capital. Tight 1% band → **−$557 (no-go)**. Sit-wide 16% → **+$29 / +$25** train/holdout. Race 16/0.5 holdout → **+$24**. ML ranker shadow-only until more snapshot days.

## Code freeze

Registration/hackathon refine through **2026-09-30**; entry cemented **2026-10-01**; race **2026-10-06**. Record every trial in `docs/TRIALS_LEDGER.md`.
