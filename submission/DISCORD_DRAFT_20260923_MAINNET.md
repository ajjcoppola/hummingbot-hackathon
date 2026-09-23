# Discord draft — 2026-09-23 mainnet smoke (facts only)

**Orca / Solana** — Agent Builders Cup (CoriolisDrift)

Checkpoint today:

- Screened pools before joining (`docs/POOL_SCREEN_GATE.md` / T008). Shortlist winner: Orca SOL-USDC Whirlpool `Czfq3xZZ…` (~$141M/24h class volume).
- Funded Gateway wallet `2ZuShDjg…` (~100 USDC + SOL gas).
- Live **mainnet** `lp_rebalancer` smoke @ width **1.5%** / trigger **0.8%** / quote **100** (T009). Position in-range; fees accruing. Reporter `T009_mainnet_100_20260923`.
- Devnet overnight was quiet HOLD (T007) — useful harness, not a fee market. Staying mainnet-only for proof.
- Condor/Gemini = status Q&A only. LLM does **not** place or cancel LP.

Charts: Orca / GeckoTerminal / DexScreener on `Czfq3xZZ…`.

No audited race P&L / Sharpe until a closed ledger window. Params unchanged until T009 baseline exists.
