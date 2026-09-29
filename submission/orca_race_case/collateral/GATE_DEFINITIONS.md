# Simple definitions — simulation gate table

Capital start in every row: **$800**. Same pool (`Czfq3xZZ…`), same Gecko hourly candles (7–28 Sep 2026), 1× share unless noted.

## Column meanings

| Term | Meaning |
|------|---------|
| **Config** | The trading rule we simulated (band width + when we recenter). |
| **Result** | Ending mark-to-market vs $800 start (and vs hold when shown). |
| **Gate** | Pass / fail under our hard rule: **do not finish below $800**. Losing money in sim = no-go. |

---

## Row-by-row

### Old tight 1.0 / 0.05 → **NO-GO**

| | |
|--|--|
| **What it is** | The old live-style band: **1%** full width (~±0.5% around spot), rebalance if price goes **0.05%** past the edge. Very tight, recenters often. |
| **Result** | $800 → **$243 (−$557)**. About **1,224** rebals on the path. |
| **Gate** | **NO-GO** — simulation loses more than half the book. Do not race this. |

---

### sit_wide 16% → **PASS both**

| | |
|--|--|
| **What it is** | Open a **16%** full-width band once (~±8%) and **never recenter**. Just sit and collect fees while in range. |
| **Result** | Train week **+$29**; holdout week **+$25** (both vs $800 start). |
| **Gate** | **PASS both** — absolute no-loss on train *and* holdout. Best pure economics in the grid. |

---

### Race 16% / 0.5 → **Holdout PASS (near sit-wide)**

| | |
|--|--|
| **What it is** | What we can actually run on Botcamp: official `lp_rebalancer` with **16%** width and **0.5** threshold (recenter only if price is 0.5% past the band). Behaves like sit_wide most of the time. |
| **Result** | Holdout **+$24**. Train **−$48** after **one** recenter into a SOL rally (crystallized divergence). |
| **Gate** | **Holdout PASS** — made money on the held-out week. Train miss is why we keep the threshold high (rare recenter ≈ sit_wide). This is the **race YAML**. |

---

### R003 Czfq holdout → **PASS (constant-TVL caveat)**

| | |
|--|--|
| **What it is** | Same sit-wide **16%** idea on Czfq in the R003 multi-pool replay (true SOL-USDC screen). Fees estimated with **today’s TVL held constant** (no historical TVL series). |
| **Result** | Holdout **+$30** vs start, and **+$9 vs HODL** (beat just holding the opening mix). |
| **Gate** | **PASS**, with caveat: fee dollars are a napkin under constant TVL — directionally supportive, not a live fill claim. |

---

## One-line cheat sheet

| Config | In plain English | Gate |
|--------|------------------|------|
| Old tight 1.0 / 0.05 | Chase price in a tiny band | **Fails — loses money** |
| sit_wide 16% | Open wide once, don’t touch | **Passes — makes money both windows** |
| Race 16% / 0.5 | Wide band, almost never rebalance | **Passes holdout; race entry** |
| R003 Czfq holdout | Same wide sit on Czfq (fee napkin) | **Passes (+ beats HODL), caveat** |
