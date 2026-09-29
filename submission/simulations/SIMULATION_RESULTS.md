# Tags

`market-making` `lp` `orca` `solana` `gateway` `whirlpools` `clmm` `simulation`

## Exchanges

Orca (primary). Eligible venue: Solana.

## Description

This agent holds **one** concentrated SOL/USDC position on Orca Whirlpool `Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE` (0.04% fee). Execution is official Hummingbot V2 `lp_rebalancer` + Gateway `orca/clmm`.

### Simulation gate (required)

Losing money in simulation is a **no-go**. Same Gecko hourly path, $800 start, 1× share:


| Config                   | Holdout end | PnL vs $800            | Verdict                               |
| ------------------------ | ----------- | ---------------------- | ------------------------------------- |
| Old tight **1.0 / 0.05** | $243        | **−$557**              | **NO-GO** (1,224 rebals)              |
| **sit_wide 16%**         | $825        | **+$25** (train +$29)  | **PASS** both windows                 |
| Race **16% / 0.5**       | $824        | **+$24**               | Holdout PASS (near sit-wide; 1 rebal) |
| R003 Czfq holdout        | $830        | **+$30** (+$9 vs HODL) | PASS (constant-TVL caveat)            |


Full grid (310 train configs), no-loss survivors, curves, and ML shadow status: `submission/simulations/`.

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


| Parameter                 | Race value | Note                     |
| ------------------------- | ---------- | ------------------------ |
| `position_width_pct`      | 16.0       | Full band (~±8%)         |
| `rebalance_threshold_pct` | 0.5        | Rare recenter ≈ sit_wide |
| `total_amount_quote`      | 800        | Botcamp custody          |
| `autoswap`                | true       |                          |
| `pool_address`            | Czfq3xZZ…  | Orca API only            |




## Status

Simulation pack attached. Live R003m in progress (ledger). T016 cancelled. Entry freeze 2026-10-01; race 2026-10-06.

## Events

Range open / hold in-band / rare rebalance past 0.5% threshold. Fee accrual drives Volume.





## Grid search (R002)

- **310** train configs screened (widths 1–16, triggers 0.05–3, caps, skew, gates).
- Absolute no-loss on **both** train and holdout: **3** configs (see `no_loss_gate.json`) — led by **sit_wide 16%**.
- Holdout leaderboard (top absolute PnL): `holdout_grid_leaderboard.json`.
- Full grid: `r002_cup_grid.json` · equity curves: `r002_curves.json`.



### Race executable (maps to sit_wide economics)

Official `lp_rebalancer` cannot “never rebalance”; **16% width + 0.5 threshold** recentered **once** on holdout, finished **$824.23** (+$24.23), fees $13.38, median 48h edge vs hold **+$0.38**. That is the race YAML (`configs/lp_rebalancer_race_800.yml`).

## R003 multi-pool

- Corrected R002’s OR-filter mislabel; true SOL-USDC universe only.
- Hard-filter switcher stayed on Czfq (0 switches); holdout ≈ sit-wide **+$30** vs start.
- Artifact: `r003_multi_pool.json`.



## ML intensity ranker

```
status: SHADOW_ONLY_INSUFFICIENT_DATA
snapshots: 6
promote_ready: False
note: insufficient_examples n=0 need>=24
```

Ridge next-24h intensity model is **shadow-only** until snapshot history covers held-out days. It does **not** pick the race band. See `ml_shadow_status.json`.

## Honest limits

- Sims are fee napkins + CLMM mark-to-market, not live fills.
- R003 fees use **constant TVL**.
- Train window for 16/0.5 lost absolute dollars after a recenter — the race relies on the threshold staying high so behavior stays near sit_wide.
- Live proof **R003m** ($100, 16/0.5) started 2026-09-28 ~01:27Z — not a finished P&L claim.



## Reproduce

```bash
python3 research/cup_money_search.py
python3 research/r003_multi_pool_replay.py
python3 -c "from orca_tight_range.ml_intensity import shadow_from_log; print(shadow_from_log('data/pool_snapshots.jsonl'))"
```

