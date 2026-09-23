# Botcamp strategy form — paste-ready

Use these fields on [https://www.botcamp.xyz](https://www.botcamp.xyz) (New Strategy / Hackathon application). All markdown is allowed in the long fields.

## Strategy Type

Agent - AI/autonomous trading agent

(If the form also accepts Controller, pick **Controller** as a second tag: the runnable artifact is a Hummingbot V2 controller. Condor is optional narration only.)

## Summary

Tight-range Whirlpool market maker on Orca that maximizes fee capture per dollar via aggressive ±1–2% concentrated liquidity, directional range-skewing, a flush-exhaustion filter, and offline parameter search before live Gateway deployment.

## Tags

`market-making` `lp` `orca` `solana` `gateway` `whirlpools` `clmm`

## Exchanges

Orca (primary). Eligible venue: Solana.

## Description

This agent implements an active, tight-range concentrated liquidity market making strategy on **Orca Whirlpools (Solana)**, targeting **SOL/USDC**. Instead of a passive full-range LP, it holds an ultra-narrow tick range (±1–2% of spot). A ±1% band is on the order of **200x** the capital efficiency of a full-range position; ±5% is still ~40x — the closest thing to leverage on a spot AMM without borrowing.

When price exits the current range, the agent closes the position and immediately reopens a new tight range centered on the updated price. A directional skew module biases the band using short-term momentum. A **volatility-exhaustion filter** defers re-centering during a one-bar flush so the agent does not lock in realized IL at the worst print. A **gas cap** (`max_rebalances_per_hour = 6`) and a **15% drawdown kill-switch** keep the 48-hour race from death-spiraling.

Net objective for the race window: **Fees − Realized IL − Gas**, not long-horizon IL minimization.

The LLM never places trades. Policy is deterministic Python (`src/orca_tight_range/logic.py`). Hummingbot `LPExecutor` + Gateway execute on-chain. Offline research (pandas / optional zipline-reloaded) only writes YAML parameters.

## Markets

- **Primary venue:** Orca Whirlpools via Hummingbot Gateway (`lp_provider: orca/clmm`)
- **Primary pair:** SOL/USDC (0.30% fee tier; adaptive fees in vol)
- **Network:** `solana-mainnet-beta` for the race; `devnet` for dry runs
- **Research data only (no execution):** Binance SOL/USDT OHLCV for range/rebalance search
- **Not used (US ToS):** Binance Global, Gate, Bitget, Hyperliquid, Derive



## Parameters


| Parameter                        | Default | Description                                                         |
| -------------------------------- | ------- | ------------------------------------------------------------------- |
| `range_width_pct`                | 1.5     | Half-width of the tick band around spot (±1.5%)                     |
| `skew_bias`                      | 0.6     | Fraction of the band on the momentum-favored side (0.5 = symmetric) |
| `rebalance_trigger_pct`          | 0.8     | Min deviation from center before a reopen is allowed                |
| `volatility_exhaustion_window_s` | 300     | Lookback used to tell a flush from a trend                          |
| `max_rebalances_per_hour`        | 6       | Gas / MEV cap                                                       |
| `capital_allocation_usdc`        | 800     | Race starting capital (Botcamp-funded)                              |
| `stop_loss_drawdown_pct`         | 15      | Hard halt                                                           |




## Status

Mainnet Orca SOL-USDC smoke live (T009 — ~$100 quote on Whirlpool `Czfq3xZZ…`; see `docs/TRIALS_LEDGER.md`). Devnet Gateway open→close→reopen proven earlier (T001–T003). Official `lp_rebalancer` + `orca/clmm` is the unattended race path; custom `orca_tight_range` policy shares the same width/trigger defaults. Code freeze was 2026-08-31; live ops stay ledger-honest (no P&L claims without a trial row).

## Events

- `RangeOpened` — new Whirlpool position (center, tick bounds)
- `RangeExited` — price left the band; evaluate rebalance
- `RebalanceExecuted` — old position closed, new tight band opened
- `RebalanceDeferred` — exhaustion filter blocked a flush recenter
- `RateLimited` — gas cap hit
- `StopLossTriggered` — 15% drawdown; agent halted



## Video Link

```
https://www.loom.com/share/687d7c1047534d259b19a4807ea0ef61
```

Images for Flowchart & Images: `submission/images/01_architecture.png`, `02_decision_loop.png`, `03_venue_and_wallets.png`.

## Team ranking

1. **Orca**
2. Meteora (same Gateway / Solana LP path if Orca seats fill)



## One-paragraph team application (if they ask "why Orca")

I am applying to race for Orca with a tight-range Whirlpool LP on SOL/USDC. The 48-hour finals reward fee-per-dollar, not multi-week IL minimization, so the agent concentrates liquidity in a ±1–2% band, recenters when price leaves, and refuses to recenter into a one-bar flush. Execution is Hummingbot Gateway `orca/clmm` plus the official LP executor — the same stack Orca already sponsors. I am a US person, so CEX sponsors and Hyperliquid/Derive are ToS-off-limits; Orca is the legal, on-theme venue.