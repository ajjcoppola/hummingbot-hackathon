# Morning eval — 2026-09-25 (filled)

**Pulled:** 2026-09-25 ~16:32Z. Reporter T011 still up; watchdog restarted (had died overnight).

## 0. Overnight facts

| Metric | Value |
|--------|-------|
| Bot uptime | **100%** (`orca_tight_mainnet_smoke-20260924-213341`) |
| Window | ~**18.9 h** (T011 clean marks) |
| Close→open | **7** total since T010 recycle; **2** after ~05:11Z sleep |
| In-range % | **46%** full window; **~15%** overnight (mostly OOR) |
| Fees | end pending ~**$0.015** USDC (+ dust SOL); max pending seen ~$0.155 (resets on rebal) |
| Clean Δ MTM overnight | **+$0.59** (~$120.7 → ~$121.3) |
| FAILED-open spam / orphan | none observed; **1 bot / 1 LP** |
| Gas / free SOL | free SOL **0.092 → 0.175** (+0.083; rent refunds / closes) |

### Money in → money out (true capital)

| | USDC-equiv |
|--|------------|
| **Money in** | **$119.56** = 100.25 USDC + 0.16535 SOL × $116.77 (deposit-day mark) |
| **Money out now** | **~$121.30** (wallet + LP + pending fees @ spot ~121.53) |
| vs money-in | **+$1.74 (~+1.5%)** |
| vs HODL same bag | **+$0.95** (HODL now ~$120.35) |

Chart: canvas `morning-eval-money-in-out` + hourly series in that file.

### Live blocker (do before param A/B)

LP `gvVUtyJs…` band **[114.56, 116.31]** while spot **~121.53** (~4.5% above upper). With threshold 0.05, auto-close should fire near **~116.37**. Stuck OOR past limit **~8+ h**. Capital is safe (mostly free USDC + quote-side LP) but **not earning fees** and **not racing volume**.

```bash
python3 scripts/mainnet_bot_ops.py soft-restart
# wait ~2–3 min → status
# if still past-limit OOR:
python3 scripts/mainnet_bot_ops.py adopt --recycle --restart-gateway
```

---

## 1–2. Decision

**Primary lane: Cup** (finals Oct 1; volume + P&L).

| Order | Action |
|-------|--------|
| 1 | Unstick past-limit HOLD (soft-restart → recycle) |
| 2 | **T012 / C1:** `position_width_pct: 1.5 → 1.0`, keep `rebalance_threshold_pct: 0.05`, quote $100 |
| 3 | 4–8h window: success = n_rebals≥2, in-range>40%, **no** >1h past-limit OOR |

**Invest path (not this morning):** after unstick, I1 widen 2–3% or hold and measure fee−gas for a week.

---

## 3. Out of scope

Custom controller, Condor `/agent` LP, venue switch — unchanged.

---

## 4. Noon deliverable checklist

- [x] Section 0 filled  
- [x] Lane = Cup + C1 (after ops)  
- [x] Next trial = T012 width 1.0  
- [x] Success metrics listed  
- [x] Money-in chart  

Ledger: update T011 overnight note; add T012 when width change deploys.
