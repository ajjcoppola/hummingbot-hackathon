# Mainnet tomorrow — funding, execution, metrics, strategy knobs

Date target: **2026-09-23 (Wed) morning**. Venue stays **Orca / Solana only**. Policy stays in `src/orca_tight_range/logic.py` / official `lp_rebalancer` — no second brain, no Condor LLM LP.

Overnight Devnet (tonight): `total_amount_quote: 77` on pool `3KBZiL2…`, wallet `2ZuShDjg…`. Reporter + watchdog + digest stay up; review tearsheet in the morning before mainnet.

**Pool gate (do before funding/deploy):** run [`research/orca_pool_screener.py`](../research/orca_pool_screener.py) and complete [`POOL_SCREEN_GATE.md`](POOL_SCREEN_GATE.md). Research row **T008** (2026-09-23): screen **PASS** on SOL-USDC `Czfq3xZZ…` — deploy still waits on mainnet funding. Full pack: [`MORNING_ANALYSIS_20260923.md`](MORNING_ANALYSIS_20260923.md).

---

## 1. Funding (do first, before any mainnet OPEN)

| Need | Amount | How |
|------|--------|-----|
| SOL (gas + LP base) | ~0.1–0.2 SOL | Buy on Kraken (or similar) → withdraw **Solana** to `2ZuShDjgEkdiTtEqbSSCzGUhh5kaFqMjhiuC2VPUNXoB` |
| USDC | **~100 USDC** | Same exchange → Solana network → same address |

Checks before deploy:

1. Condor `/gateway` → network **solana-mainnet-beta** (not Devnet).
2. Balances show SOL + USDC on that wallet (API `portfolio/state` or Gateway wallets).
3. Helius **mainnet** `nodeURL` still set (already applied via `scripts/apply_helius_rpc.py --mainnet`); never commit the key.
4. Confirm pool still valid: Orca SOL-USDC whirlpool `Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE` (0.04% fee) — already in [`configs/lp_rebalancer_mainnet_smoke.yml`](../configs/lp_rebalancer_mainnet_smoke.yml).

Tax: every mainnet fill is taxable. Keep tx signatures in `docs/TRIALS_LEDGER.md`.

---

## 2. Execution sequence (morning)

1. **Stop / leave Devnet bot flat or holding** — do not run Devnet + mainnet on the same wallet concurrently without a clear plan (duplicate inventory / RPC load).
2. Health gate: OrbStack → API `:8000` → Gateway `:15888` → Condor → MQTT bot status `running` after deploy.
3. POST config `orca_tight_mainnet_smoke` from YAML (`total_amount_quote: 100`, width 1.5, trigger 0.8).
4. Deploy `lp_rebalancer` with **no** $10 drawdown kill (`max_*_drawdown_quote` null).
5. Prove one OPEN via `positions_owned` + explorer tx; then leave unattended with reporter.
6. LLM / Gemini: status Q&A only — **never** place/cancel LP.

If Gateway `/gateway/swap/execute` 404s again (API path skew), use the pattern in `scripts/devnet_swap_sol_to_devusdc.py` adapted for mainnet SOL-USDC / `Czfq3xZZ…`, or Condor Gateway UI.

---

## 3. Performance measurement (what “good” means tomorrow)

Capture the same dual-source pack as Devnet:

| Artifact | How |
|----------|-----|
| Snapshots / MTM | `research/devnet_run_reporter.py` (reuse; rename run-id `T00x_mainnet_…`) |
| Watchdog | `research/devnet_watchdog.py` with mainnet network/wallet/prefix overrides if needed |
| Digest | `research/devnet_health_digest.py` |
| Tearsheet | `research/make_tearsheet.py --run-id …` |
| Ledger row | One row per param change / session in `docs/TRIALS_LEDGER.md` |

Report honestly (no P&L claim without a ledger row):

- Uptime %, n rebalances, fees collected (base/quote), rent/gas, MTM Δ, in-range %, failed txs / 429s
- Volume proxy: sum of notional on open/close/swap events (race score cares about volume)
- IL proxy: MTM vs HODL same inventory (approximate from snapshots)

Morning review checklist: finalize overnight Devnet tearsheet → decide promote / hold / tighten for mainnet.

---

## 4. Strategy adjustments (volume vs returns)

Baseline (tonight + first mainnet smoke): **width 1.5% / trigger 0.8% / offset −0.01** — matches race defaults. Record every change as a new trial ID.

### To push **volume** (more fee events / more scored turnover)

Try one change at a time; 1–2h each; ledger before/after:

| Knob | Direction | Why | Risk |
|------|-----------|-----|------|
| `position_width_pct` / `range_width_pct` | **Tighten** (e.g. 1.5 → 1.0 → 0.75) | Price leaves band more often → more rebals | More gas + IL; Helius 429 under burst |
| `rebalance_threshold_pct` / `rebalance_trigger_pct` | **Lower** (0.8 → 0.5) | Recenter sooner after drift | Whipsaw / fee bleed |
| `max_rebalances_per_hour` (orca_tight_range) | **Raise** carefully (6 → 8) | Allow more turns in vol | Gas death spiral |
| Pool fee tier | Prefer **higher fee** whirlpool if TVL still deep | More fee/$ when in range | Less flow / worse fills |

### To push **returns** (fee − gas − IL)

| Knob | Direction | Why | Risk |
|------|-----------|-----|------|
| Width | **Widen** slightly (1.5 → 2.0) | Stay in range longer; fewer gas hits | Lower fee velocity / volume |
| Trigger | **Raise** (0.8 → 1.0) | Fewer rebals | Larger IL if trend runs |
| Exhaustion / flush filter (orca_tight_range) | Keep on | Avoid recenter into flush | Miss some vol spikes |
| Capital | Stay **$100** until green | Limits blast radius | Slow learning |

**Rule:** optimize for the 48h race objective (volume + P&L), not Sharpe. Deflate any overnight “edge.” Prefer promoting a setting only if fees − gas look non-negative **and** volume is up vs baseline on the same window length.

Policy home: if using custom controller, edit `logic.py` only; if staying on official `lp_rebalancer`, only YAML knobs above. Do not ask Condor `/agent` to trade.

---

## 5. Suggested Wed morning order of operations

1. Digest + tearsheet overnight Devnet @ 77  
2. Re-run pool screener + confirm [`POOL_SCREEN_GATE.md`](POOL_SCREEN_GATE.md) still PASS (T008 baseline: `Czfq3xZZ…`)  
3. Fund mainnet wallet (SOL + 100 USDC)  
4. Mainnet smoke 15–30 min @ 100, same 1.5 / 0.8  
5. If stable: 2–4h run + tearsheet  
6. Optional: **one** volume knob (tighter width) for a short A/B, ledger T00x  
7. Discord update from ledger facts only (`submission/DISCORD_DRAFT_*.md`)

---

## Explicit non-goals

No Gate/Bitget/HL, no inventing `pool_address`, no committing keys/RPC secrets, no LLM execution, no claiming Botcamp-custodied $800 as personal capital.
