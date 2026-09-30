# Demo video script — wide-band race entry (2.5–4 min)

For Botcamp strategy **156** / application refresh. Replaces the old ±1.5% / “200× leverage” Loom.

**Goal:** prove the agent is running unattended on Orca mainnet with the **race-shaped** config, and that the sim no-loss gate is why we chose **16% / 0.5**.

**Do not claim:** finished 48h P&L, Botcamp race win, or that Volume = your own open/close swaps.

---

## 0. Prep (before record)

- Amphetamine on; bot healthy:
  ```bash
  python3 scripts/mainnet_bot_ops.py status
  # expect: ok true, 1 running bot, 1 in-range LP, position_info PASS
  ```
- Browser tabs ready:
  1. Repo: https://github.com/ajjcoppola/hummingbot-hackathon
  2. Chart image or PDF: `submission/orca_race_case/images/orca-race-case.png`
  3. Solana Explorer (mainnet) for LP:  
     https://explorer.solana.com/address/5nNNxiXiX4qdvnGYLeFgHHuivWLqZnDD5q8uAbtbcZBh  
     *(update address if status shows a new position)*
  4. Optional Condor `/lp` or `/web` — narration only
- On-screen files to flash: `configs/lp_rebalancer_race_800.yml`, `configs/lp_rebalancer_r003m_100.yml`, `submission/simulations/SIMULATION_RESULTS.md`

---

## 1. Title card (5s)

**On screen:**  
`Orca Wide-Band SOL/USDC Farmer — Agent Builders Cup — live proof`

**Say:**  
“This is our Agent Builders Cup entry for Orca: a wide-band Whirlpool LP, not a tight-band churn bot.”

---

## 2. Why we changed the thesis (35–45s)

**Show:** `orca-race-case.png` (the cup-800-sim chart).

**Say (verbatim-ish):**

“We ran an offline no-loss gate on Gecko hourly SOL-USDC with eight hundred dollars start.

The old tight band — one percent width, aggressive recenter — finished around two hundred forty-three dollars: minus five hundred fifty-seven. That’s a no-go.

Sitting wide at sixteen percent finished plus about twenty-five on holdout. The race YAML — sixteen percent width, zero-point-five rebalance threshold — finished about plus twenty-four with almost no rebals.

So the race entry is wide band, rare recenter. Volume for Botcamp is fees-implied traded volume — not our own open and close swaps.”

**Point at table rows:** NO-GO red / PASS green / race blue.

---

## 3. Architecture in one breath (25s)

**Show:** `configs/lp_rebalancer_race_800.yml` (and optionally R003m `$100` proof YAML).

**Say:**

“Execution is official Hummingbot V2 `lp_rebalancer` plus Gateway `orca/clmm` on mainnet. Pool is Czfq — the only true SOL-USDC tier that cleared our TVL filter for an eight-hundred deposit. Condor and any LLM are narration only — they never place or cancel LP.”

---

## 4. Live proof — the required clip (90–120s)

**Show terminal:**

```bash
cd ~/proj/hummingbot-hackathon
python3 scripts/mainnet_bot_ops.py status
tail -1 data/mainnet_watchdog/watchdog.jsonl
```

**On screen, call out:**

- `ok: true`
- one running bot (`orca_tight_mainnet_smoke-…`)
- one position, `in_range: true`
- band ~16% (lower/upper vs spot)
- pending fees (tiny is fine — honesty)
- watchdog line: `detail: healthy`

**Show Explorer** on the live position address.  
**Say:** “This is the same unattended loop we’ll run for the forty-eight-hour race: open a wide range, hold in-band, recenter only if price breaches the half-percent threshold past the edge.”

Optional 10s: flash `git log -1 --oneline` on `main` (Beta-Checkpoint) and `pytest tests/test_watchdog_flat.py -q`.

---

## 5. Honesty / freeze (15s)

**Say:**

“Live proof is R003m at about one hundred dollars while we finish the application. Race book is eight hundred on Botcamp custody. We do not claim unfinished-clock P&L. Entry freeze October first; race October sixth. Code and sims are in the public repo and under Code Files.”

---

## 6. Close (5s)

**On screen:**  
`github.com/ajjcoppola/hummingbot-hackathon` · `submission/simulations/`

**Say:** “Wide band, fees-implied volume, Gateway execution — that’s the entry.”

---

## Shot checklist (keep under 4:00)

| # | Shot | Time |
|---|------|------|
| 1 | Title | 0:00–0:05 |
| 2 | Sim chart + no-loss table | 0:05–0:50 |
| 3 | Race YAML + pool address | 0:50–1:15 |
| 4 | `status` + watchdog healthy | 1:15–2:45 |
| 5 | Explorer position | 2:45–3:15 |
| 6 | Freeze / repo / close | 3:15–3:45 |

---

## Upload

1. Record Loom or YouTube **unlisted**.
2. Paste URL into Botcamp strategy **Video Link** (field in `submission/FORM_PASTE.md`).
3. Replace the old Loom if it still sells ±1.5% / 200× leverage.

## Do not say

- “We’re up X% on the race” (race hasn’t started; proof is ~$100)
- “Tight band = free leverage”
- “LLM manages the LP”
- Any CEX venue (Gate / Bitget / Binance Global / Hyperliquid / Derive)
