# Botcamp form paste — strategy 156 (race bot 16% / 0.5)

URL: https://www.botcamp.xyz/dashboard/strategies/156  
Source of truth: `submission/orca_race_case/collateral/APPLICATION.md`  
Deadline: **EOD 2026-09-30**. Freeze 2026-10-01. Race 2026-10-06.

Copy each block into the matching field. Upload `submission/simulations/` under Code Files.

---

## Name / Title

```
Orca Wide-Band SOL/USDC Farmer
```

*(If the portal already named this strategy “Orca Tight-Range Leverage Farmer”, keep that title and replace Summary/Description/Parameters below — do not invent a second strategy.)*

---

## Strategy Type

**Agent** / Controller (Hummingbot V2). Condor is narration only — it does not trade.

---

## Summary

```
Wide-band Orca SOL/USDC Whirlpool LP on Czfq3xZZ…: 16% width, 0.5 rebalance threshold. Simulation no-loss gate: old 1% band −$557 (rejected); sit-wide 16% +$29/+$25 train/holdout; race YAML 16/0.5 holdout +$24. Volume = fees-implied traded volume. Deterministic lp_rebalancer + Gateway. LLM does not trade. See submission/simulations/.
```

---

## Tags

```
market-making, lp, orca, solana, gateway, whirlpools, clmm, simulation
```

---

## Exchanges

```
Orca (primary). Eligible venue: Solana.
```

---

## Description

```
This agent holds one concentrated SOL/USDC position on Orca Whirlpool Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE (0.04% fee). Execution is official Hummingbot V2 lp_rebalancer + Gateway orca/clmm.

Simulation gate (required): Losing money in simulation is a no-go. Same Gecko hourly path, $800 start, 1× share:
- Old tight 1.0/0.05 → holdout $243 (−$557) — NO-GO (1,224 rebals)
- sit_wide 16% → train +$29 / holdout +$25 — PASS both windows
- Race 16%/0.5 → holdout $824 (+$24), 1 rebal, fees ~$13 — Holdout PASS
- R003 Czfq holdout → $830 (+$30, +$9 vs HODL) — PASS (constant-TVL caveat)

Full grid (310 train configs), no-loss survivors, curves, ML shadow status: submission/simulations/.

Thesis: Tightening a CLMM band scales fees and loss-versus-rebalancing together — not free leverage. Wide band + rare recenter keeps capital above start while collecting fees. True SOL-USDC tier screen (tokensBothOf) finds only Czfq above $500k TVL for an $800 deposit. Botcamp Volume (40%) = traded volume implied by fees earned (not own open/close swaps).

Live: Proof run R003m ($100, 16/0.5) started 2026-09-28 after cancelling tight-band T016. No unfinished-clock P&L claimed. Race capital on Botcamp is $800 (configs/lp_rebalancer_race_800.yml). LLM never places or cancels LP.
```

---

## Markets

```
- Orca Whirlpools via Gateway orca/clmm
- SOL/USDC on Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE (0.04%)
- solana-mainnet-beta
- Not used: Binance Global, Gate, Bitget, Hyperliquid, Derive
```

---

## Parameters

```
| Parameter | Race value | Note |
| --- | --- | --- |
| position_width_pct | 16.0 | Full band (~±8%) |
| rebalance_threshold_pct | 0.5 | Rare recenter ≈ sit_wide |
| total_amount_quote | 800 | Botcamp custody |
| autoswap | true | |
| pool_address | Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE | Orca API only |
```

---

## Status

```
Simulation pack attached under Code Files (submission/simulations/). Live R003m proof ($100, 16/0.5) after cancelling T016. No unfinished-clock P&L claimed. Entry freeze 2026-10-01; race 2026-10-06.
```

---

## Events

```
Range open / hold in-band / rare rebalance when spot moves >0.5% past band edge. Fee accrual drives Volume (fees-implied traded volume).
```

---

## Video Link

```
https://www.loom.com/share/687d7c1047534d259b19a4807ea0ef61
```

Re-record if the Loom still sells ±1.5% / “200× leverage”. Race chart image: `submission/orca_race_case/images/orca-race-case.png`.

---

## Code / attachments checklist

1. `submission/simulations/` (SIMULATION_RESULTS.md + JSON)
2. `configs/lp_rebalancer_race_800.yml` + `configs/lp_rebalancer_r003m_100.yml`
3. `submission/strategy.md` (or `submission/orca_race_case/collateral/strategy.md`)
4. `src/orca_tight_range/` + `controllers/`
5. `research/cup_money_search.py`, `research/r003_multi_pool_replay.py`
6. `docs/TRIALS_LEDGER.md`, `docs/RULES_DIGEST.md`
7. Public repo: https://github.com/ajjcoppola/hummingbot-hackathon
8. Chart: `submission/orca_race_case/images/orca-race-case.png`
