# Demo video script — record this for Botcamp (2.5–4 min)

**File to open while recording:** this doc.  
**Strategy page:** [https://www.botcamp.xyz/dashboard/strategies/156](https://www.botcamp.xyz/dashboard/strategies/156)  
**Public repo:** [https://github.com/ajjcoppola/hummingbot-hackathon](https://github.com/ajjcoppola/hummingbot-hackathon)  

Replaces the old Loom (±1.5% / “200× leverage”).

**Product title (say once, keep Botcamp name):** *Orca Tight-Range Leverage Farmer*  
**Subtitle you must explain:** race entry is now **wide-band 16% / 0.5**, not a tight churn band.

**Goal:** (1) show why sims forced the algo change, (2) show the unattended mainnet bot running that race shape.

**Do not claim:** finished 48h race P&L, Botcamp win, or Volume = your own open/close swaps.

---



## 0. Prep (60 seconds before record)

Run this and leave the terminal visible:

```bash
cd ~/proj/hummingbot-hackathon
python3 scripts/mainnet_bot_ops.py status
tail -1 data/mainnet_watchdog/watchdog.jsonl
git log -1 --oneline
```

**Expect right now (2026-09-30):**


| Check    | Value                                                  |
| -------- | ------------------------------------------------------ |
| `ok`     | `true`                                                 |
| Bot      | `orca_tight_mainnet_smoke-20260929-202448` **running** |
| LP       | `5nNNxiXiX4qdvnGYLeFgHHuivWLqZnDD5q8uAbtbcZBh`         |
| Band     | ~109.45 – 128.49 (~16%), `in_range: true`              |
| Watchdog | `detail: healthy`                                      |
| HEAD     | `2e55c61` (or newer on `main`)                         |


**Browser tabs (in this order):**

1. GitHub README (chart embeds here): [https://github.com/ajjcoppola/hummingbot-hackathon](https://github.com/ajjcoppola/hummingbot-hackathon)
2. Local chart (bigger): `submission/orca_race_case/images/orca-race-case.png`
3. Explorer LP: [https://explorer.solana.com/address/5nNNxiXiX4qdvnGYLeFgHHuivWLqZnDD5q8uAbtbcZBh](https://explorer.solana.com/address/5nNNxiXiX4qdvnGYLeFgHHuivWLqZnDD5q8uAbtbcZBh)
4. Optional: Condor `/lp` — **view only**, do not close/open

**Editor tabs to flash:**  
`configs/lp_rebalancer_race_800.yml` · `configs/lp_rebalancer_r003m_100.yml`

If `status` shows a **different** position address, use that Explorer URL instead.

---



## 1. Title (0:00–0:08)

**On screen:** GitHub repo title + README subtitle.

**Say:**

“This is our Agent Builders Cup Orca entry — still titled Orca Tight-Range Leverage Farmer on Botcamp, but the race subtitle is a wide-band SOL/USDC Whirlpool farmer: sixteen percent width, zero-point-five rebalance threshold.”

---



## 2. Why we changed the algo (0:08–0:55)

**Show:** README simulation section, or zoom `orca-race-case.png`.

**Say:**

“We kept the product name, but we changed the policy after a no-loss simulation gate on Gecko hourly data with an eight-hundred-dollar start.

The old tight one-percent band finished around two hundred forty-three dollars — minus five hundred fifty-seven. That’s a hard no-go.

Sitting wide at sixteen percent finished about plus twenty-five on holdout. The executable race YAML — sixteen percent by zero-point-five — finished about plus twenty-four with almost no rebals.

So for the Cup we run wide band, rare recenter. Botcamp Volume is fees-implied traded volume — not our own open and close swaps.”

**Point at the table:** red NO-GO → green PASS → race 16/0.5.

---



## 3. What actually executes (0:55–1:20)

**Show:** `configs/lp_rebalancer_race_800.yml` (scroll `position_width_pct: 16.0`, `rebalance_threshold_pct: 0.5`, pool `Czfq3xZZ…`).

**Flash:** `configs/lp_rebalancer_r003m_100.yml` — “same band, one-hundred-dollar live proof.”

**Say:**

“Execution is official Hummingbot V2 lp_rebalancer plus Gateway orca/clmm on mainnet. Pool Czfq is the only true SOL-USDC tier that cleared our TVL filter for an eight-hundred deposit. Condor and any LLM are narration only — they never place or cancel LP.”

---



## 4. Live proof clip — required (1:20–3:10)

**Show terminal** (`status` + watchdog). Call out on camera:

- `ok: true`
- one running bot ending in `…202448`
- one LP, `in_range: true`
- lower/upper ≈ 109.45 / 128.49 vs spot ~119–120
- pending fees (small is fine — be honest)
- watchdog: `healthy`

**Switch to Explorer** on `5nNNxiXi…`.

**Say:**

“This is the unattended loop for the forty-eight-hour race: open a sixteen-percent range, hold in-band and earn fees, and only recenter if price moves more than half a percent past the edge. Same shape as the eight-hundred race book; this proof run is about one hundred dollars.”

Optional 8s: `git log -1 --oneline` showing the docs/Beta-Checkpoint commit.

---



## 5. Freeze / honesty (3:10–3:35)

**Say:**

“We do not claim unfinished-clock P&L. Application deadline is end of day September thirtieth. Entry freeze October first; race October sixth. Code, sims, and this chart are in the public GitHub repo and under Botcamp Code Files.”

---



## 6. Close (3:35–3:45)

**On screen:** repo URL.

**Say:** “Wide band, fees-implied volume, Gateway execution — that’s the entry.”

---



## Shot checklist


| #   | Shot                        | Time      |
| --- | --------------------------- | --------- |
| 1   | Title + subtitle            | 0:00–0:08 |
| 2   | Sim chart / no-loss table   | 0:08–0:55 |
| 3   | Race YAML 16 / 0.5          | 0:55–1:20 |
| 4   | `status` + healthy watchdog | 1:20–2:40 |
| 5   | Explorer LP                 | 2:40–3:10 |
| 6   | Deadline / repo close       | 3:10–3:45 |


---



## After recording

1. Upload Loom or YouTube **unlisted**.
2. Paste URL into Botcamp → strategy 156 → **Video Link**.
3. Delete / replace the old Loom if it still sells ±1.5% or 200× leverage.



## Do not say

- “We’re up X% on the Cup race” (proof ≠ race book)
- “Tight band equals free leverage”
- “The LLM manages the LP”
- Gate / Bitget / Binance Global / Hyperliquid / Derive

