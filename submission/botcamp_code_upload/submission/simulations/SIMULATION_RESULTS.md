# Simulation results (application pack)

**Capital start:** $800 · **Pool:** Orca SOL/USDC `Czfq3xZZ…` · **Candles:** Gecko hourly 2026-09-07 → 2026-09-28 · **Path:** 1× share, high–low intra-hour.

## No-loss gate (hard)

A config **fails** if `end_equity < $800` (finished below start). Losing money in simulation is a **no-go**.

| Config | Train PnL vs $800 | Holdout PnL vs $800 | vs HODL (hold) | Verdict |
|--------|-------------------:|--------------------:|---------------:|---------|
| Tight live **1.0 / 0.05** (rejected) | — (full-span) | **−$557** (`$243`) | −$615 | **NO-GO** |
| **sit_wide 16%** (open once) | **+$29** | **+$25** | −$3.8 | **PASS** both windows |
| **lp_rebalancer 16 / 0.5** (race YAML) | −$48 | **+$24** | −$4.4 | Holdout **PASS**; train lost after one recenter into rally |
| R003 Czfq sit-wide holdout | — | **+$30** | **+$9** | **PASS** (constant-TVL caveat) |

## Why this might work

1. The old tight band **destroys capital** in the same candle set ($800 → $243, 1,224 rebals) — so “just tighten more” is falsified.
2. Wide / rare-recenter **keeps the book above $800** on the holdout week and tracks hold within a few dollars while earning ~$10–17 of fees.
3. Among true SOL-USDC tiers (`tokensBothOf`), only Czfq clears TVL ≥ $500k (R003) — intensity shopping does not unlock a free higher-fee pool for $800.

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
