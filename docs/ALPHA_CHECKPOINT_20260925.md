# Alpha Checkpoint — 2026-09-25

Tag: `alpha-checkpoint`

## What this marks

Working mainnet Orca SOL-USDC tight-range path on official `lp_rebalancer` + Gateway:

- Pool `Czfq3xZZ…`, wallet `2ZuShDjg…`, quote ~$100, width **1.5%**, `rebalance_threshold_pct` **0.05**
- Ops: `scripts/mainnet_bot_ops.py` (status / soft-restart / hard-restart / adopt / adopt --recycle)
- Watchdog: `research/mainnet_health_watchdog.py` — **past-limit → adopt --recycle** (not soft-restart)
- Sherlock: `docs/SHERLOCK_REBALANCE_20260924.md`
- Morning eval + money-in chart notes: `docs/MORNING_EVAL_20260925.md`

## Known failure mode (fixed in ops)

Gateway `SIMULATION_FAILED` on close → executor FAILED → controller **halts** with LP still open. Soft-restart then tries a second OPEN → `INSUFFICIENT_BALANCE`. Recovery is Gateway close + redeploy (`adopt --recycle`).

## Endurance window after this tag

Reporter run-id: `T012_mainnet_100_endurance_20260925` (target ≥48h to emulate Cup finals length). Params unchanged at checkpoint; width tighten (C1 → 1.0) is a later trial after endurance baseline.
