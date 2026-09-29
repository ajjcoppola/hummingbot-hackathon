# Botcamp page update — paste now (deadline EOD 2026-09-30)

Target: https://www.botcamp.xyz/strategies/orca-tight-range-leverage-farmer

**Must upload with code:** `submission/simulations/` (grid + no-loss gate + ML shadow).

## Summary (replace)

Orca SOL/USDC LP on `Czfq3xZZ…`, **16%** band / **0.5** threshold. Simulation no-loss gate: old 1% band finishes **−$557** (rejected); sit-wide 16% finishes **+$29 / +$25** train/holdout; race YAML 16/0.5 holdout **+$24**. Volume = fees-implied traded volume. Deterministic `lp_rebalancer` + Gateway. LLM does not trade.

## Description (replace)

One concentrated SOL/USDC position on Orca Whirlpool `Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE`. Unattended path: Hummingbot `lp_rebalancer` + Gateway `orca/clmm`.

**Simulation (Gecko hourly 7–28 Sep 2026, $800, 1× share):** Losing money in sim is a no-go. Tight 1.0/0.05 → **$243 (−$557, 1,224 rebals)**. Sit-wide 16% → train **+$29**, holdout **+$25**. Executable race shape 16%/0.5 → holdout **$824 (+$24)**, 1 rebal, fees ~$13. R003 holdout napkin **+$30** and **+$9 vs HODL** (constant-TVL caveat). Grid: 310 train configs; absolute no-loss survivors in `submission/simulations/no_loss_gate.json`. ML intensity ranker is **shadow-only** (insufficient snapshot history to promote).

**Live:** R003m proof ($100, 16/0.5) after cancelling T016. Race book uses quote **800**. No unfinished-clock P&L claims.

## Parameters

| Parameter | Value |
| --- | --- |
| `position_width_pct` | 16.0 |
| `rebalance_threshold_pct` | 0.5 |
| `total_amount_quote` | 800 race / 100 R003m |
| `pool_address` | Czfq3xZZ… |

## Status

Sims attached under Code Files → `submission/simulations/`. Live R003m started 2026-09-28. Freeze 2026-10-01; race 2026-10-06.

## Resources

- `submission/simulations/SIMULATION_RESULTS.md`
- `configs/lp_rebalancer_race_800.yml`
- `research/cup_money_search.py`, `research/r003_multi_pool_replay.py`
- `docs/TRIALS_LEDGER.md`
