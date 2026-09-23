# Botcamp form paste — AGENT strategy (2026-08-27)

URL: https://www.botcamp.xyz/dashboard/strategies/new?type=AGENT

Honest vs the early Perplexity-era blurb: **same venue and tight-range idea**; **live path is Gateway + `lp_rebalancer` / `LPExecutor` on Devnet today**; custom `decide()` policy is in-repo and unit-tested; **zipline tuning was skipped** for the freeze window (pandas/toy sim + Devnet txs instead).

Copy each block below into the matching field. Leave Video Link blank until Loom/YouTube is ready.

---

## Name / Title

```
Orca Tight-Range Leverage Farmer
```

---

## Strategy Type

Select: **Agent** (page already `type=AGENT`).

If there is a secondary type / tag for the runnable artifact, also mark **Controller** (Hummingbot V2). Condor is harness only — LLM does not place LP.

---

## Summary

```
Tight-range Orca Whirlpool LP on Solana that maximizes fee-per-dollar in a short race window via ±1.5% concentrated RANGE liquidity, automated close/reopen when price leaves the band, and Hummingbot Gateway execution (LPExecutor / lp_rebalancer). Deterministic policy in Python; LLM never places or cancels LP.
```

*(Old summary implied zipline-validated params before live. New: Devnet open→close→reopen proven; zipline grid deferred past freeze.)*

---

## Tags

```
market-making, lp, orca, solana, gateway, whirlpools, clmm, rebalancer
```

---

## Exchanges / Markets (short field)

```
Orca Whirlpools (Solana) via Hummingbot Gateway orca/clmm. Primary race pair: SOL/USDC on mainnet. Dry-run: SOL-devUSDC on solana-devnet.
```

---

## Description (main long field — replaces your old “Trading agent description”)

```
This agent implements an active, tight-range concentrated liquidity market making strategy on Orca Whirlpools (Solana), targeting SOL/USDC for the race and SOL–devUSDC for Gateway dry runs.

Rather than a passive full-range LP, it maintains an ultra-narrow RANGE around spot (default ±1.5%) to maximize capital efficiency and fee capture per dollar. When price exits the band (beyond a rebalance threshold), the position is closed and a new tight band is opened around the updated price — turning AMM LP into active market making for a 48-hour scored window (Volume / P&L / HBOT Vote).

Architecture (what is actually implemented):
- Policy: deterministic decide() in src/orca_tight_range/logic.py (unit-tested). Events include RangeOpened, RebalanceExecuted, RebalanceDeferred (flush/exhaustion filter), RateLimited (max 6 reb/hour), StopLossTriggered (15% drawdown).
- Execution: Hummingbot LPExecutor + Gateway lp_provider orca/clmm. Condor (/gateway, /lp, /bots, /web) is the local harness; the LLM must not place or cancel LP.
- Unattended race path: official generic lp_rebalancer controller with position_width_pct=1.5, rebalance_threshold_pct=0.8, side=RANGE, autoswap enabled (see configs/lp_rebalancer_devnet.yml). Custom orca_tight_range controller wraps the same policy for drop-in when the bot image can import it.
- Proven on Devnet: open → close → reopen on Whirlpool 3KBZiL2g8C7tiJ32hTv5v3KM7aK9htpqTw4cTXz1HvPt (logged in docs/TRIALS_LEDGER.md T001–T003). No fabricated mainnet P&L.

US-person venue gate: Orca / Solana only. Not used: Gate, Bitget, Binance Global, Hyperliquid, Derive.

Net objective for the race window: Fees − Realized IL − Gas — not long-horizon IL minimization. A ±1% band is on the order of ~200x the capital efficiency of a full-range position (“leverage” on a spot AMM without borrowing).
```

---

## Markets (long / structured field if separate)

```
- Venue: Orca Whirlpools (CLMM) via Hummingbot Gateway (`lp_provider: orca/clmm`)
- Race network: solana-mainnet-beta — pair SOL/USDC (prefer deep fee tier; confirm pool_address before freeze)
- Dry-run network: solana-devnet — pair SOL-devUSDC — pool 3KBZiL2g8C7tiJ32hTv5v3KM7aK9htpqTw4cTXz1HvPt (~0.20%)
- Executor: Hummingbot LPExecutor; controller: lp_rebalancer (official) / orca_tight_range (policy wrapper)
- Research-only (no execution): optional OHLCV for offline sims; zipline parameter grid deferred — not blocking submission
- Forbidden for this entry (US ToS): Binance Global, Gate, Bitget, Hyperliquid, Derive
```

---

## What makes this unique (if the form has this field — else fold into Description)

```
Most LP bots optimize for long-horizon IL via wide ranges. This entry is optimized for Botcamp’s short evaluation window: tight ±1–2% Whirlpool bands, unattended close/reopen via Gateway, and race scoring (fee/volume throughput over multi-week IL minimization).

vs a generic “passive LP” bot:
1) Active recenter when out of range (not set-and-forget).
2) Deterministic risk guards in policy code (exhaustion defer, gas cap, 15% kill-switch) — not LLM discretion on orders.
3) Same stack Orca sponsors (Gateway orca/clmm + LPExecutor), with a Devnet open/close/reopen already on-chain before freeze.

Honesty note: early materials mentioned zipline-reloaded validation before live; for the Aug 31 freeze we shipped unit-tested policy + Devnet Gateway txs and kept official lp_rebalancer as the runnable unattended path. Offline zipline remains optional research, not a claim of live edge.
```

---

## Parameters

```
| Parameter | Default | Live / Devnet mapping | Description |
|---|---|---|---|
| range_width_pct / position_width_pct | 1.5 | lp_rebalancer + logic.Params | Half-width of band around spot (±1.5%) |
| rebalance_trigger_pct / rebalance_threshold_pct | 0.8 | same | Min move beyond band before close/reopen |
| skew_bias | 0.6 | logic.Params (custom controller) | Momentum skew; 0.5 = symmetric |
| volatility_exhaustion_window_s | 300 | logic.Params | Flush filter lookback |
| max_rebalances_per_hour | 6 | logic.Params | Gas / MEV cap |
| stop_loss_drawdown_pct | 15 | logic.Params / bot drawdown | Hard halt |
| capital_allocation_usdc / total_amount_quote | 800 race / 20 Devnet | Botcamp $800 finals; tiny Devnet size | Quote notional |
| side | RANGE | lp_rebalancer | Double-sided in-band LP |
| position_offset_pct | -0.01 | Devnet YAML | Slight in-range offset; autoswap fills deficit |
| autoswap | true | Devnet YAML | Swap via network swapProvider when unbalanced |
| lp_provider | orca/clmm | required | Orca Whirlpools |
| connector_name | solana-devnet (dry) / solana-mainnet-beta (race) | Gateway network id | Not the DEX name |
```

---

## Status

```
Devnet Gateway loop proven (open → close → reopen on Orca SOL–devUSDC; TRIALS_LEDGER T001–T003). Unattended path: official lp_rebalancer + orca/clmm; custom orca_tight_range policy shares width/trigger defaults and is unit-tested. Code freeze 2026-08-31. No live mainnet P&L claimed.
```

---

## Events

```
- RangeOpened — new Whirlpool position (center, tick bounds)
- RangeExited — price left the band; evaluate rebalance
- RebalanceExecuted — old position closed, new tight band opened
- RebalanceDeferred — exhaustion filter blocked a flush recenter
- RateLimited — gas cap (max rebalances/hour) hit
- StopLossTriggered — 15% drawdown; agent halted
- Hold — in-range; collect fees
```

---

## Video Link

```
https://www.loom.com/share/687d7c1047534d259b19a4807ea0ef61
```

Images: upload PNGs from `submission/images/` (architecture, decision loop, venue/wallets).

---

## Code / attachments (upload checklist)

Upload `submission/botcamp_code_upload.zip`, which includes:

- `submission/strategy.md`
- `src/orca_tight_range/logic.py`
- `controllers/orca_tight_range_controller.py`
- `configs/lp_rebalancer_devnet.yml`
- `docs/INSTALL_PLAN.md`
- `docs/TRIALS_LEDGER.md`
- `research/orca_backtest_zipline.py` + `zipline_to_gateway_bridge.py`

---

## Team ranking (hackathon application, if separate from this form)

```
1. Orca
2. Meteora (same Gateway / Solana LP path if Orca seats fill)
```

---

## Diff vs your old Botcamp blurb (one glance)

| Old claim | Now |
|---|---|
| Tight ±1–2% Orca SOL/USDC | Same intent; Devnet uses SOL-devUSDC pool `3KBZiL2…` |
| Directional skew + active recenter | Policy in `logic.py`; live unattended = `lp_rebalancer` RANGE + threshold 0.8 |
| Zipline-validated before live | Skipped for time; unit tests + Devnet txs are the evidence |
| “Prepared with Perplexity Deep Research” | OK as research credit; do not imply Perplexity runs the bot |
| Passive AMM LP | Still true — emphasize Gateway txs + freeze date |
