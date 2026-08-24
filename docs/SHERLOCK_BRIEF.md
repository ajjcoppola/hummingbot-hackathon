# Sherlock brief — feasible Agent Builders Cup entry

Date: 2026-08-23. Protocol: 6-step Sherlock Mode.

## Step 1 — Reflect (failure modes)

1. **Wrong venue for a US person** — CEX sponsors + Hyperliquid + Derive ToS.
2. **Wrong deadline** — Perplexity Aug 15 "registration only" note is stale; rules of record freeze **Aug 31**.
3. **Scope explosion** — Coinbase V2 upgrade, zipline live hybrid, IB, Condor-places-orders.
4. **Stale local Hummingbot (2024)** — no current Gateway CLMM / `lp_executor`.
5. **Empty form** — Botcamp wants Type / Summary / Description / Markets / Parameters / Events / **code files** / **video**.
6. **Unrunnable unique controller** — custom code that never talks to Gateway.
7. **Look-ahead research** — fitting range width on the same 48h you "backtest."

## Step 2 — Distill (most likely)

1. **Venue + ToS** (highest impact, easy to test: Orca/Meteora/XRPL only).
2. **Eight-day feasibility** — official `lp_rebalancer` + `orca/clmm` is the runnable core; our logic is a thin policy on top.
3. **Submission completeness** — video + `strategy.md` + code, not a manifesto.

## Step 3 — Investigate

- Official rules (resources page, all 11 articles).
- Perplexity pack (Botcamp 13 guide, US legal, DEX vs CEX, tight-range Whirlpool, Aug 15 checklist, form draft, code-file list).
- Hummingbot Orca CLMM endpoints + `LPExecutorConfig` + `controllers/generic/lp_rebalancer` (default `lp_provider: orca/clmm`).
- User choice: **Orca** (not XRPL).
- Local trees: `~/proj/hummingbot` dated July 2024.

## Step 4 — Analysis

| Claim | Verdict | Evidence |
|-------|---------|----------|
| Must race on Gate/Binance to be eligible | False | Rule 06 includes Solana; Orca is a sponsor |
| US person can ToS-safely use Gate/Bitget/Hyperliquid/Derive | False | Perplexity legal note + Derive terms |
| Aug 15 was the last day | Stale | Rule 01/09: apply + freeze Aug 31 |
| Need Condor LLM to place trades | False | Rule 05: controller and agent race equally; LLM-in-the-loop is a risk |
| Need zipline live | False | Perplexity itself put zipline in **offline** Phase 2 |
| 2024 checkout is enough | False | LP executor is v2.13+; Orca CLMM pricing fix v2.13; hackathon stack is v2.16 |
| Tight range wins 48h on fee/dollar | Plausible | Perplexity Whirlpool note; still need gas/IL model |
| Official lp_rebalancer already targets Orca | True | Default `lp_provider: orca/clmm` |

Recommended architecture: **deterministic policy** (`logic.py`) → **V2 controller** → **LPExecutor** → **Gateway/Orca**. Zipline/pandas only write YAML. Condor optional, never signs txs.

## Step 5 — Suggestions

- Log every `Event` from `logic.py` in the live controller (already `logger.info`).
- One trials row per width/trigger change (`TRIALS_LEDGER.md`).
- Devnet first. Do not debug policy on mainnet gas.
- If Gateway slip: freeze official `lp_rebalancer` and keep our `strategy.md` honest about it.

## Step 6 — Cleanup

No temporary debug hooks were added beyond normal `logger.info`. Nothing to remove after a fix.

## Perplexity files folded in

| File | Used as |
|------|---------|
| `Hummingbot Botcamp 13 Guide.md` | Markets, US legal, hybrid-as-offline-only |
| `Asking about the hummingbot bot camp agent competi.pdf` | Venue gate |
| `Comparing DEX vs CEX...pdf` | Why LP/fee-per-dollar not CEX PMM |
| `Competitive Strategy: Tight-Range Whirlpool...pdf` | Core strategy |
| `Ok, the deadline...pdf` | Portal urgency (dates corrected to Aug 31) |
| `Need to fill in: Describe the trading agent...pdf` | Application paragraph |
| `Ok. start the project...pdf` | Form field map |
| `Need code files and an install plan...pdf` | The four artifacts |
