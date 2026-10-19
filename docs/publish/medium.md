---
title: In and Out | The Orca Cup
tags: [investing, crypto, solana, market-making]
canonicalUrl: https://investitnow.substack.com
---

# In and Out | The Orca Cup

InvestIt Now — Alan & Jeff

**Series index** (one letter; paste whole or split by part)

1. [Part I — The shadow](#part-i--the-shadow)
2. [Part II — What the Orca drivers did](#part-ii--what-the-orca-drivers-did)
3. [Part III — What we tried after the fact, and what failed](#part-iii--what-we-tried-after-the-fact-and-what-failed)
4. [Part IV — Flush & Fade: an In/Out alpha for Orca](#part-iv--flush--fade-an-inout-alpha-for-orca)
5. [Part V — How you make money on an Orca SOL-USDC pool](#part-v--how-you-make-money-on-an-orca-sol-usdc-pool)
6. [Part VI — Condor on Telegram, API in the race](#part-vi--condor-on-telegram-api-in-the-race)
7. [Part VII — Key findings](#part-vii--key-findings)

## TLDR

- We ran a **48-hour shadow** of the Hummingbot Agent Builders Cup on **Orca SOL-USDC** (Whirlpool `Czfq3xZZ…`, 0.04% fee). SOL fell about **8%**. Our naked wide-band LP lost **6.64%** — about **−$53** on an $800 book (a linear scale of our ~$158 shadow; we did not deposit $800).
- Orca’s two official drivers lost **−0.59%** (Victor Adeleke) and **−1.82%** (Hoang La) on live $800 with similar volume. They stepped out of or reshaped their inventory. We did not.
- After the fact we replayed **27 days** of real 5-minute Czfq data, with fees calibrated from our own on-chain positions. Always-on LP, tight bands, and even fast trend switches lost money in the Cup. On this pool, **fees roughly equal the LP’s loss to arbitrage**, so being IN is not an edge by itself.
- What did work, with rules chosen on **pre-Cup data only**, is **Flush & Fade**: sit in USDC, and only after a high-volume flush buy SOL and sell the bounce back through a SOL-only Orca band that earns fees on the way up. Replay: **+0.41%** in the Cup window (ahead of both drivers), **+7.8%** over 27 days while SOL fell **8.1%**, max drawdown **3.7%**.
- It is **7 trades**. We show every one, and the parameter that could have flipped the Cup result. This is a research result, not live P&L.

---

# Part I — The shadow

## Economic thesis

Concentrated liquidity on a big pool looks like “market making for yield.” The honest payoff is:

**Net LP return ≈ fees − divergence loss.**

A wide band still holds SOL. When SOL trends one way, you underwrite that move, and 0.04% fees are a thin premium for doing it. In InvestIt terms the Cup shadow was **all IN with no OUT**.

## What we did

**Venue.** Orca Whirlpools on Solana mainnet, SOL/USDC, pool address from Orca’s API. For a US person, self-custodial DEX only.

**Shell.** Offline work showed tight bands look busy and fail on trends, so the live shell became a **16%** band that recenters only after price leaves it. Deposit a SOL/USDC mix, collect fees while spot stays inside, hold.

**Host.** A Mac ran the Cup start and stop timers on the shadow wallet (~$158). Measurement run on the real clock, not Botcamp’s $800 deposit.

## 48-hour results (shadow), then the $800 scale

| Arm | Close (shadow) | Return |
|-----|----------------|--------|
| Hold USDC | $158.08 | 0.00% |
| 50/50 SOL/USDC hold | ~$151.80 | −4.0% |
| Naked 16% LP (what we ran) | $147.59 | **−6.64%** |

SOL in the window: **$118.81 → $109.38 (−7.9%)**. Fees on the LP: about **$0.63** (fee-implied volume ~$1,600).

**$800 column = linear scale of the shadow** (`× 800 / 158.08`). Same returns; not a deposit we made.

| Arm | Close @ $800 | P&L @ $800 | Return |
|-----|--------------|------------|--------|
| Hold USDC | $800 | $0 | 0.00% |
| 50/50 hold | ~$768 | ~−$32 | −4.0% |
| Naked LP | ~$747 | **~−$53** | **−6.64%** |

Scaled fees about **$3.20**; scaled fee-implied volume about **$8,000**. Contest volume is not wallet profit.

## Why that was wrong for the goal

1. **Wrong payoff model.** Being in a huge pool is not “printing.” Fees minus divergence matched the result.
2. **No OUT.** All capital in the band, through a grind and then a crash.
3. **Fee budget too small.** Sixty cents of fees cannot insure an 8% move.
4. **Score ≠ wallet.** We collected volume and lost to cash and to a plain 50/50 hold.

---

# Part II — What the Orca drivers did

We were a shadow, not a selected driver. The public [Agent Builders Cup leaderboard](https://www.botcamp.xyz/hackathons/agent-builders-cup-1) (fetched 2026-10-17) still answers the question: **who lost less when SOL dumped?**

Each live agent started with **$800**. Score = 2× P&L points + 2× Volume points + 1× HBOT vote points. Orca’s team vote was **4.7M HBOT (rank 1)**, which lifts both Orca **scores**. The wallet lesson is **P&L**.

| Who | 48h P&L | Volume | Mechanism (Botcamp strategy card) |
|-----|---------|--------|-----------------------------------|
| **Victor Adeleke**, Adaptive Orca LP | **−0.59%** | $4,973 | One Whirlpool. Width from live volatility; **withdraw when vol is extreme**; rebalance only if fees beat cost. |
| **Hoang La**, Trend-Aware LP Rebalancer | **−1.82%** | $7,031 | **Condor + Hummingbot.** Rank pools, set the next range from **trend**; controller executes between agent cycles. |
| Our naked shadow (scaled) | **−6.64%** | ~$8,000 | Fixed 16% band, never withdrew. |
| Hold USDC | 0% | $0 | The OUT. |
| Neil Mascarenhas, Regime Switch LP *(Meteora, contrast only)* | +0.00% | $209 | Standing aside beat a bad LP. |

Same order of volume (~$5–8k), very different inventory. They did not “win the dump”; they **lost less by refusing or reshaping inventory**. One honest footnote: when we coded rough replicas of their rules, our versions did **not** reproduce their Cup results (our replicas lost −5.2% and −3.1%). Their real execution details matter, so we compare to their **board numbers only**.

Also ours to own: our public Botcamp card still describes an older **±1.5% tight farmer**; the shadow ran **16%**.

---

# Part III — What we tried after the fact, and what failed

We rebuilt the weekend with real data instead of opinions:

- **Price and volume:** 27 days of 5-minute candles for Czfq (Sep 21 – Oct 17), split into **pre-Cup** (training), **Cup** (48h holdout), and **post-Cup** (8-day holdout).
- **Fees:** calibrated from **our own on-chain LP fee accrual** — what one unit of our liquidity actually earned per dollar of pool volume. We use the pre-Cup calibration so the Cup does not leak into the fee level (the Cup itself paid ~50% more per unit, so this is conservative).
- **Check:** the replay of our naked 16% LP loses **−5.65%** in the Cup vs **−6.64%** real (the gap is idle wallet SOL the shadow carried).

What failed, and why it matters:

| Idea | Cup 48h (replay) | Lesson |
|------|------------------|--------|
| Always-on LP, any width from 0.5% to 16% | −5.2% to −15.4% | Tighter = more fees **and** more loss. Width is not the lever. |
| Fast trend In/Out (15-minute to 2-hour signals), 3,600 variants | **0 of 3,600 positive** | A faster switch does not help. The 36-hour grind moved in noise-sized steps, so every fast signal whipsawed. |
| Chop LP between events for extra volume | adds volume, subtracts return | Volume you pay for is not alpha. |
| Park OUT money in Orca USDC/USDT LP | ~0.8% APR today | Not worth the complexity; OUT = USDC. |
| Cash sleeve + −3% equity kill (our first draft) | −3.5% | Only lost less. Dropped. |

The core finding: on Czfq, **fees roughly equal the LP’s loss to arbitrage** across all three windows. Being IN is not an edge by itself. Edge has to come from **when** you provide liquidity, and on which side.

---

# Part IV — Flush & Fade: an In/Out alpha for Orca

## Thesis

Liquidity is cheap most of the time and scarce in a flush. When SOL drops fast on heavy volume, forced sellers (liquidations, stops, panic) overshoot, and whoever **takes the other side right after** gets paid by the snap-back. On Orca we can do that and still earn LP fees: buy the flush, then **sell the bounce through a single-sided SOL band** above entry. The band is a limit sell that earns 0.04% as it fills. The rest of the time we are OUT, in USDC.

## The rule

| Step | Rule |
|------|------|
| **OUT (default)** | Hold USDC. No LP. |
| **Arm** | SOL down **≥ 3% over 6 hours** on **≥ 2×** that span’s normal volume (trailing day). |
| **IN** | Wait for a **0.8%** lift off the post-flush low; swap the book to SOL. |
| **Exit band** | Put the SOL in a **SOL-only Orca band from entry to +2%**. As price recovers through it, SOL sells for USDC and earns swap fees. |
| **OUT again** | Band fully converted (target), or **24h** time stop, or **4%** hard stop. Back to USDC. |

All parameters were picked on **pre-Cup data only**, then frozen.

## Results (replay, $800 book, pre-Cup fee calibration)

| Window | SOL | 50/50 hold | Naked 16% LP | **Flush & Fade** | F&F fees | F&F fee-implied volume |
|--------|-----|------------|--------------|------------------|----------|------------------------|
| Pre-Cup, Sep 21 – Oct 7 (train) | +6.6% | +3.3% | +4.0% | **+4.6%** | $24.53 | $61k |
| **Cup 48h (holdout)** | −6.9% | −3.5% | −5.7% | **+0.41%** | $1.75 | $4.4k |
| Post-Cup, Oct 9 – 17 (holdout) | −6.2% | −3.1% | −3.1% | **+1.6%** | $7.07 | $17.7k |
| **All 27 days, continuous** | **−8.1%** | −4.0% | −6.0% | **+7.8%** | $36.73 | $92k |

At $800: **~$803** at the end of the Cup window (vs Victor ~$795, Hoang ~$785, our real shadow ~$747), and **~$863** after 27 days. Max drawdown over 27 days: **3.7%** (naked LP: 11.8%). With the Cup’s own fee level the Cup result is +0.53%.

Chart and every trade: [orca-cup-who-lost-less.canvas.tsx](/Users/ajjc/.cursor/projects/Users-ajjc-proj-hummingbot-hackathon/canvases/orca-cup-who-lost-less.canvas.tsx).

## Every trade

| Entry (UTC) | SOL in | Exit (UTC) | SOL out | Book P&L | Exit | Window |
|-------------|--------|------------|---------|----------|------|--------|
| 09-23 16:05 | 114.64 | 09-24 16:05 | 116.09 | +1.83% | time | train |
| 09-28 10:50 | 118.45 | 09-29 10:50 | 119.39 | +1.90% | time | train |
| 09-30 20:20 | 118.02 | 10-01 20:20 | 118.34 | +0.80% | time | train |
| 10-08 15:40 | 109.02 | 10-09 11:45 | 111.58 | +1.50% | target | **Cup** (marked +0.41% at window close) |
| 10-13 01:00 | 103.46 | 10-13 02:10 | 105.64 | +1.00% | target | post |
| 10-14 14:55 | 104.31 | 10-15 14:55 | 104.71 | +0.56% | time | post |
| 10-16 17:30 | 103.68 | 10-17 17:30 | 103.26 | +0.01% | time | post |

The Cup trade bought the 15:00Z crash at about $109, sat through a further dip to ~$105.6 (−3.1%, inside the 4% stop), and was back above entry when the 48 hours ended.

## Why it might be luck (read this)

- **Seven trades.** All winners. Only three were in the training window. That is a small sample; some of this is luck.
- **The stop was not identifiable before the Cup.** On pre-Cup data every stop from 2% to 6% scored the same. We took the middle (4%). A **2% stop** would have stopped out the Cup trade and turned the window into **−1.5%**.
- **Neighbors.** Moving one parameter at a time to its neighboring values, **94%** of variants stay positive over 27 days (median +5.2%). The Cup turns negative if the trigger is looser (a 2–2.5% drop, or no volume filter), the entry lift is smaller (0.3–0.5%), or the stop is tight (2%).
- **Volume is modest.** In the Cup, fee-implied volume (~$4.4k) is about Victor’s, below Hoang’s and below our naked LP. A back-of-envelope Cup score with +0.41% (rank ~6 on P&L) and ~$4.4k volume lands near Victor’s, not at the top. The point is the wallet, not the vote.
- **Model limits.** Fees assume pool depth like the period we calibrated on; fills are at 5-minute closes with 0.05% swap cost.

## How it maps to the official controller

The exit band is something Hummingbot’s `lp_rebalancer` already does: **`side: SELL`** with **`position_offset_pct: 0`** and **`position_width_pct: 2`** puts a SOL-only band just above spot. What is new is the **slow policy** that decides *when*: arm on a flush, enter on the lift, stand down after target/time/stop. That belongs in our shared policy module before any live trial.

---

# Part V — How you make money on an Orca SOL-USDC pool

Large TVL means **someone is willing to be the bid and the offer**. Who gets paid:

1. **Swappers / flow traders** pay 0.04% for instant SOL↔USDC. They win when their edge elsewhere beats that toll.
2. **Orca** takes a protocol cut of every fee, whether or not any LP beats a hold.
3. **LPs** win only when fees beat divergence. On Czfq that is roughly a coin flip before costs, so passive, always-on LP is a beta bet with a small fee rebate.
4. **Whoever supplies liquidity when it is scarce.** After a flush, buyers are scarce and the snap-back pays them. That is the market-making edge Flush & Fade harvests — liquidity offered at the moment it is worth most, then the LP band used as a fee-earning limit sell.

The In/Out translation:

| | Old (Cup shadow) | New (Flush & Fade) |
|---|---|---|
| Default | IN: 50/50 band, always | **OUT: USDC** |
| When IN | All the time | Only after a high-volume flush |
| How LP is used | Symmetric inventory sink | **Single-sided exit**: sell the bounce, earn fees |
| What protects you | Nothing | Time stop, hard stop, and mostly being OUT |

What we name and reject for this stack:

| Idea | Why not here |
|------|--------------|
| CEX / perp delta hedge | Executable strategy stays Orca / Solana. |
| Arb swarm | Different P&L stream; does not fix LP inventory. |
| JIT liquidity / mempool sniping | Real research topic; not something we can run honestly. |
| Stablecoin LP as the OUT | ~0.8% APR on Orca USDC/USDT today. |

---

# Part VI — Condor on Telegram, API in the race

**What we did.** Condor on Telegram (`/agent`, `/lp`) was our **build harness and viewer**. During the Cup the process was **Hummingbot API + `lp_rebalancer` + LaunchAgents**. The LLM never placed or cancelled LP — by design.

**Good.** Unattended, deterministic execution. No chatbot click opening positions.

**Bad.** We switched the supervisor off and froze a fixed 16% band. Nothing could change the stance when the grind turned into a crash. Hoang kept Condor in the loop to set the next range between controller cycles.

**Verdict.** API-only **execution** was right. API-only **policy** was the miss. Flush & Fade is exactly the kind of slow decision a supervisor should make — arm, enter, stand down — while `lp_rebalancer` keeps doing the fills. The supervisor should be deterministic code (Condor as the Telegram shell and alerting), not an LLM placing trades.

---

# Part VII — Key findings

- On Czfq, **fees ≈ the LP’s loss to arbitrage**. Always-on LP is a SOL bet; tighter bands and faster trend switches did not fix that in the Cup (0 of 3,600 fast-switch variants were positive).
- Victor (**−0.59%**) and Hoang (**−1.82%**) beat our shadow (**−6.64%**) by stepping out of or reshaping inventory. Vote points are not wallet alpha.
- **Flush & Fade** — USDC by default, buy only after a high-volume flush, sell the bounce through a fee-earning SOL-only band — replays at **+0.41%** in the Cup and **+7.8%** over 27 days while SOL fell 8.1%, with rules chosen before the Cup. Seven trades: promising, not proven.
- Condor-for-build plus API-for-fills was half right. Next trial: a deterministic policy that decides *when* (Flush & Fade), with the official controller doing the fills, logged in the trials ledger before any live claim.

## In closing

The Cup did not fail because Orca is broken. It failed because we stayed IN without an OUT, on a pool where simply being IN pays about nothing. The fix is not a wider band or a faster switch. It is In and Out applied to liquidity itself: stay OUT, and be the liquidity only when the market is paying for it.

InvestItNow — Alan & Jeff

---

> Remember, investing involves risk, and past performance is not indicative of future results. Please consult with a financial advisor before making any investment decisions. None of the information we present to you is personal investment advice. The Cup figures for our strategy are a 48-hour shadow run scaled linearly to $800; Flush & Fade results are an offline replay (7 trades over 27 days) with modeled fees and costs; finalist figures are from the public Botcamp leaderboard as of 2026-10-17. We were not a selected Cup driver. None of this is a promise of future returns.
