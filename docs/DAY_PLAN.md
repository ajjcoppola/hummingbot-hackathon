# Aug 24–31 build calendar

Today is **Sun 2026-08-23**. Freeze is **Mon 2026-08-31**.

| Day | Outcome | Done when |
|-----|---------|-----------|
| Sun 23 | Application in | Orca apply + strategy form + video URL + this repo attached |
| Mon 24 | Fresh stack | Condor + Hummingbot API Docker + Gateway container; `/gateway` Solana **devnet** |
| Tue 25 | First on-chain loop | `/lp` or `lp_rebalancer` open → out-of-range close → reopen; log tx hashes |
| Wed 26 | Policy on chain | Custom controller or documented `lp_rebalancer` as a Condor `/bots` instance |
| Thu 27 | Parameter honesty | One CSV backtest in `data/`; trial row in `TRIALS_LEDGER.md` |
| Fri 28 | Tiny mainnet | Small SOL/USDC position; gas + fee vs model; **no size ego** |
| Sat 29 | Demo v2 | Replace tonight's test video with a Gateway clip |
| Sun 30 | Freeze candidate | YAML + `strategy.md` match; stop changing width/skew |
| Mon 31 | Submit / freeze | No logic or param edits after close; confirm portal status |

If you fall behind: **skip custom controller** and freeze official `lp_rebalancer` + `orca/clmm` + tight width. A running official controller beats an unfinished unique one.

Condor is in scope as the **harness** (`/gateway`, `/lp`, `/bots`, `/web`). Out of scope until after freeze: Coinbase V2 upgrade, zipline↔live MQTT, IB hybrid, Condor LLM order placement.
