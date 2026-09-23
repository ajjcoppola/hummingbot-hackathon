# Morning analysis pack — 2026-09-23 (pre-fund)

Venue: **Orca / Solana only**. No Devnet fee claims. No mainnet OPEN until wallet funded.

## Gate status

| Check | Result |
|-------|--------|
| Screener | **PASS** — `data/pool_screens/20260923_1131.json` (+ earlier `1125`) |
| Shortlist winner | **SOL-USDC** `Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE` |
| Fee / TVL / Vol24 | 0.04% / ~$26.1M / ~$141.7M (fees24 ~$56.7k) |
| Charts (Gecko) | **PASS** — ~125.8k txns / 24h, vol ~$141.3M, liquidity ~$26.1M, GT score 92, last tx recent |
| Gateway pool-info | **PASS** — `solana-mainnet-beta` resolves address, `fee_pct=0.04`, price ~116.77 |
| Ledger | **T008** SCREEN_PASS (research); **T006** READY_CONFIG |
| Wallet funded | **FAIL / pending** — you fund later this morning |

**Decision:** join candidate confirmed. Deploy blocked only on funding (SOL gas + ~100 USDC → `2ZuShDjgEkdiTtEqbSSCzGUhh5kaFqMjhiuC2VPUNXoB`).

### Chart links

- https://www.orca.so/pools/Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE
- https://www.geckoterminal.com/solana/pools/Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE
- https://dexscreener.com/solana/Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE
- https://dune.com/orca/orca-top-whirlpools

### Why not “better fee/$” pools (STONK / ZEC / PUMP)?

They clear volume/TVL gates but are **not same volume class** as SOL-USDC (~$5–13M vs ~$141M). First $100 smoke stays on the flagship major pair per `POOL_SCREEN_GATE.md` / race self-proof.

---

## Overnight Devnet (harness only) — T007

| Metric | Value |
|--------|--------|
| Bot | `orca_tight_devnet-20260922-220703-…` **running** (stop before mainnet) |
| Position | `BoJdNdmA…` in-range (100% of snapshots) |
| Window | ~6.4h finalized |
| Rebalances | **0** |
| Fees accrued | ~0.00034 SOL + ~0.00041 USDC (dust) |
| MTM Δ | ~−38.6 quote (mark move / inventory — **not** fee edge) |
| Artifacts | `tearsheet.md`, `report.md`, `trades.csv` under `data/devnet_runs/T007_overnight_77_20260923/` |
| Watchdog | healthy |

Do not use Devnet overnight for width/trigger promote.

---

## When you fund — mainnet-only sequence

Config ready: [`configs/lp_rebalancer_mainnet_smoke.yml`](../configs/lp_rebalancer_mainnet_smoke.yml)  
Playbook: [`MAINNET_TOMORROW.md`](MAINNET_TOMORROW.md)  
Gate: [`POOL_SCREEN_GATE.md`](POOL_SCREEN_GATE.md)

1. Re-run `python3 research/orca_pool_screener.py --tokens-both SOL,USDC` (still PASS?).
2. Condor `/gateway` → network **solana-mainnet-beta**.
3. Confirm balances: SOL + ~100 USDC on `2ZuShDjg…`.
4. **Stop Devnet bot / leave flat** — do not dual-run Devnet + mainnet on same wallet.
5. Deploy `orca_tight_mainnet_smoke` @ width 1.5 / trigger 0.8 / quote 100 — **no** $10 drawdown kill.
6. Prove one OPEN → reporter run-id `T009_mainnet_100_…` → ledger row.
7. LLM / `/agent`: Q&A only — never place LP.

Params stay 1.5 / 0.8 until a mainnet baseline row exists; tighten width only after that.
