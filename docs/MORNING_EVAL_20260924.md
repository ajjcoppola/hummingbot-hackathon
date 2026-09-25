# Morning eval — 2026-09-24 (post–T009 mainnet)

**Context:** Agent Builders Cup timeline loosened. Official Botcamp resources (fetched 2026-09-23):

| Phase | Dates | Note |
|-------|-------|------|
| Registration | May 1 – **Sep 30**, 2026 | Still open |
| Hackathon build | Aug 1 – **Oct 1**, 2026 | *Keep refining right up to the finals* |
| Selection & judging | Sep 1 – Sep 30, 2026 (**now**) | Sponsors pick; builders may still improve chosen agents |
| Finals | **Oct 1 – Oct 9**, 2026 | 48h race; winners Oct 7 (Token2049) |

Old repo “code freeze Aug 31” is **stale**. Practical deadline: harden before **Oct 1** finals start; Sep 30 is the last quiet improvement day.

Venue stays **Orca / Solana only**. LLM still must not place/cancel LP unless we deliberately change architecture (and then only within Cup rules).

---

## 0. Pull overnight facts (15 min) — filled 2026-09-24 AM

From reporter `T009_mainnet_100_20260923` + live `positions_owned`:

- [x] Uptime %: bot **100%** during 3.3h window; then reporter timeouts
- [x] Rebalances: **0** (same position address all night)
- [x] In-range %: **90.4%** in window; **now OOR** (spot ~115.67 > upper ~115.25)
- [x] Fees: ~0.19 USDC-equiv by window end; **~0.61 USDC + ~0.005 SOL** pending live
- [x] MTM Δ: **~+0.19** over window (not race P&L claim)
- [x] Failures: open-time `CloseType.FAILED:1`; overnight Gateway **timeouts**; Condor **not running**
- [x] Band still ±1.5% of open — price walked through upper; no recenter yet

**Decide:** fix ops first (Condor + why no OOR rebalance), then tune width.

---

## 1. Improvement lanes (pick 1–2, not all)

### A. Trading logic / params (highest leverage for Volume + P&L)

Race score: **Volume 40% / P&L 40% / Vote 20%**.

| Idea | Why | Risk | Ledger |
|------|-----|------|--------|
| Tighten width 1.5 → 1.0 → 0.75 | More out-of-range → more rebals → volume | Gas + IL | New T0xx each step |
| Lower rebalance trigger 0.8 → 0.5 | Recenter sooner | Whipsaw | same |
| Fee-tier / pool re-screen | Higher fee/$ if still liquid | Less flow | POOL_SCREEN_GATE |
| Exhaustion / flush filter (custom `decide()`) | Avoid recenter into flush | Miss vol | only if on custom controller |
| Kill-switch / drawdown for $800 finals | Survive 48h | Caps upside | YAML only |

**Default plan if T009 looks healthy:** one A/B — tighten width only, 2–4h, ledger before/after.

### B. Velocity via “agent swarm” (Condor multi-agent)

Cup allows **V2 Controller or Condor Agent**. We race controller path today.

Possible swarm roles (research / ops — **not** parallel LP placers on same wallet):

| Agent | Job | Boundary |
|-------|-----|----------|
| Screener | Re-run Orca API + chart gate | Writes JSON only; no OPEN |
| Risk/ops | Watch 429s, failed closes, duplicate LP | Alert / stop; no size-up |
| Narrator | Discord/status English | Q&A only |
| Tuner (optional) | Propose width/trigger from T009 stats | Human + ledger approve before YAML change |

**Do not:** N agents each opening LP on `2ZuShDjg…` (inventory collision).  
**Maybe later:** paper “swarm” proposing params → single `lp_rebalancer` executor.

### C. Strategy reevaluation from real data

Questions for morning:

1. Is SOL-USDC 0.04% still best fee/$ for *our* size, or is a mid-fee major (e.g. SOL-stable higher tier) better after T009 fee velocity?
2. Is HOLD% too high (band too wide for race volume)?
3. Is gas eating fees on every rebal at $100? Extrapolate to $800.
4. Should finals path stay official `lp_rebalancer` or promote custom `orca_tight_range` + `decide()`?

---

## 2. Out of scope tomorrow (unless data screams)

- Venue switch (Meteora/Raydium/CEX) — workspace rule
- LLM execution of LP without a written Cup-compliant design
- Claiming race P&L from a few hours of T009

---

## 3. Deliverable of the morning session

One short plan with:

1. T009 scorecard (numbers)
2. Chosen lane(s) A/B/C
3. Next trial ID + exact param/config change
4. Success metric for the next 4–24h window (fees−gas, n rebals, in-range %)

Source of truth: https://www.botcamp.xyz/hackathons/agent-builders-cup-1/resources
