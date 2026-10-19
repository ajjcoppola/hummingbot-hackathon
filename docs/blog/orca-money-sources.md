# Orca money sources — one-shot digest (2026-10-17)

Method: ai-dev-monitor style collect → score → keep only rows that change Part IV of [`in-and-out-orca-cup.md`](in-and-out-orca-cup.md). No standing `/loop`. No hca-qngn `AI_MONITOR_*.md`.

## High relevance (8+)

| Score | Source | Impact on Part IV |
|------:|--------|-------------------|
| 9 | [Tung & Wang, CLMM continuous-time / covered-call view](https://link.springer.com/article/10.1007/s42521-026-00198-z) (Digital Finance, 2026) | Concentrated LP ≈ selling time premium of an implicit call for fees. Supports **cash default**: do not sell that premium into a one-way dump. |
| 9 | Milionis et al. LVR (Loss-Versus-Rebalancing) framing (cited in above) | Fees must beat LVR / divergence — same equation as our Cup shadow. |
| 8 | [Avellaneda–Stoikov inventory control (expository 2026)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=7248442) | Reservation price skews with inventory; symmetric quotes random-walk inventory. Maps to **USDC-heavy / single-sided bids**, not 50/50 forever. |
| 8 | Victor Adeleke Adaptive Orca LP ([Botcamp strategies](https://www.botcamp.xyz/strategies)) | Live proof: vol-sized width + **withdraw when vol extreme** → −0.59% vs our −6.64%. |
| 8 | Hoang La Trend-Aware LP ([Botcamp strategies](https://www.botcamp.xyz/strategies)) | Condor sets next range from trend; controller fills → −1.82%. Policy supervisor ≠ LLM click. |

## Medium relevance (5–7)

| Score | Source | Keep? |
|------:|--------|-------|
| 7 | [Fukasawa et al., utility-indifference LP / IL unless fee](https://arxiv.org/html/2502.01931) | Reinforces fee-vs-IL; no new executable knob. |
| 6 | [JIT liquidity in CLMMs (AFT 2025)](https://doi.org/10.4230/lipics.aft.2025.8) | JIT can erode passive LP; we **reject** as our edge (honesty / ops). |
| 5 | Public Botcamp board churn / CEX MM agents | Different venues; useful only as “volume ≠ P&L” contrast. |

## Action items (for next trial, not this draft)

- [ ] Regime gate: chop + fee napkin > divergence before IN
- [ ] Vol-sized width / flat when extreme (Victor)
- [ ] Slow policy job for IN/OUT + skew; API/`lp_rebalancer` for fills
- [ ] Keep −3% equity kill as breaker only
