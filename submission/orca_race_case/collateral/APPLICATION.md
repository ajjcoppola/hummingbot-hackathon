# Botcamp strategy form — paste-ready (2026-09-28)

Deadline: **EOD 2026-09-30**. Simulation pack: `submission/simulations/SIMULATION_RESULTS.md`.

## Strategy Type

Controller (Hummingbot V2). Condor is narration only — it does not trade.

## Summary

Wide-band Orca SOL/USDC Whirlpool LP on `Czfq3xZZ…`: **16%** width, **0.5** rebalance threshold. Offline grid (R002) shows the old 1% band loses **−$557** (no-go); sit-wide 16% finishes **+$29 / +$25** on train/holdout (absolute no-loss). Race YAML matches that economics. Volume = fees-implied traded volume. LLM does not trade.

## Tags

`market-making` `lp` `orca` `solana` `gateway` `whirlpools` `clmm` `simulation`

## Exchanges

Orca (primary). Eligible venue: Solana.

## Description

This agent holds **one** concentrated SOL/USDC position on Orca Whirlpool `Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE` (0.04% fee). Execution is official Hummingbot V2 **`lp_rebalancer`** + Gateway `orca/clmm`.

### Simulation gate (required)

Losing money in simulation is a **no-go**. Same Gecko hourly path, $800 start, 1× share:

| Config | Holdout end | PnL vs $800 | Verdict |
| --- | ---: | ---: | --- |
| Old tight **1.0 / 0.05** | $243 | **−$557** | **NO-GO** (1,224 rebals) |
| **sit_wide 16%** | $825 | **+$25** (train +$29) | **PASS** both windows |
| Race **16% / 0.5** | $824 | **+$24** | Holdout PASS (near sit-wide; 1 rebal) |
| R003 Czfq holdout | $830 | **+$30** (+$9 vs HODL) | PASS (constant-TVL caveat) |

Full grid (310 train configs), no-loss survivors, curves, and ML shadow status: **`submission/simulations/`**.

### Thesis

Tightening a CLMM band scales fees and loss-versus-rebalancing together — not free leverage. Wide band + rare recenter keeps capital above start while collecting fees. True SOL-USDC tier screen (`tokensBothOf`) finds only Czfq above $500k TVL for an $800 deposit. Botcamp **Volume (40%)** = traded volume implied by **fees earned** (not own open/close swaps).

### Live

Proof run **R003m** ($100, 16/0.5) started 2026-09-28 after cancelling tight-band T016. No unfinished-clock P&L claimed. Race capital on Botcamp is $800 (`configs/lp_rebalancer_race_800.yml`).

LLM never places or cancels LP.

## Markets

- Orca Whirlpools via Gateway `orca/clmm`
- SOL/USDC on `Czfq3xZZ…` (0.04%)
- `solana-mainnet-beta`
- Not used: Binance Global, Gate, Bitget, Hyperliquid, Derive

## Parameters

| Parameter | Race value | Note |
| --- | --- | --- |
| `position_width_pct` | 16.0 | Full band (~±8%) |
| `rebalance_threshold_pct` | 0.5 | Rare recenter ≈ sit_wide |
| `total_amount_quote` | 800 | Botcamp custody |
| `autoswap` | true | |
| `pool_address` | Czfq3xZZ… | Orca API only |

## Status

Simulation pack attached. Live R003m in progress (ledger). T016 cancelled. Entry freeze 2026-10-01; race 2026-10-06.

## Events

Range open / hold in-band / rare rebalance past 0.5% threshold. Fee accrual drives Volume.

## Video Link

```
https://www.loom.com/share/687d7c1047534d259b19a4807ea0ef61
```

Re-record if the video still sells ±1.5% / “200× leverage”.

## Code / resources to upload

1. `submission/simulations/` (**SIMULATION_RESULTS.md**, grid JSON, ML status)
2. `configs/lp_rebalancer_race_800.yml` + `configs/lp_rebalancer_r003m_100.yml`
3. `submission/strategy.md`
4. `src/orca_tight_range/` + `controllers/`
5. `research/cup_money_search.py`, `research/r003_multi_pool_replay.py`
6. `docs/TRIALS_LEDGER.md`, `docs/RULES_DIGEST.md`
