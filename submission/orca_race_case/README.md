# Orca race case — Beta Checkpoint collateral

**One folder for the Botcamp selection / application conversation.** Simulation-honest and key-free.

**Product title (unchanged):** *Orca Tight-Range Leverage Farmer*  
**Race subtitle:** wide-band **16% / 0.5** on `Czfq3xZZ…` (tight ±1% rejected by no-loss gate).

## Start here (10 minutes)

1. Open **`images/orca-race-case.png`** (or **`pdf/orca-race-case.pdf`**) — no-loss table + equity chart.
2. Skim **`pdf/cup-800-sim.pdf`** — Cup money-search canvas render.
3. Paste from **`collateral/APPLICATION.md`** (or repo root `submission/FORM_PASTE.md`) into Botcamp.
4. Upload code + **`sims/`** (or the whole `submission/orca_race_case/` tree).
5. Record video from **`../VIDEO_SCRIPT_WIDE_BAND.md`**.

## Layout

| Path | Contents |
|------|----------|
| `images/` | `orca-race-case.png` / `.jpg` (page 1 chart), all-pages montage |
| `pdf/` | `orca-race-case.pdf`, `cup-800-sim.pdf` |
| `canvases/` | Cursor `.canvas.tsx` sources (cup-800-sim + prior tearsheets) |
| `sims/` | R002/R003 JSON, no-loss gate, ML shadow status, `SIMULATION_RESULTS.md` |
| `collateral/` | APPLICATION, strategy, page update, ledger, rules, Sherlock log, GATE_DEFINITIONS |
| `configs/` | Race YAML (`…_race_800.yml`) + live proof (`…_r003m_100.yml`) |

## Talking points

- **No-go:** tight 1% band → **−$557** in the same sim.
- **Pass:** sit-wide 16% → **+$29 / +$25** train/holdout absolute.
- **Race entry:** 16% / 0.5 holdout **+$24**; executable via official `lp_rebalancer`.
- **Pool:** only Czfq clears TVL gate among true SOL-USDC tiers (R003).
- **Volume:** fees-implied (not our own swaps).
- **Live:** R003m proof ($100, same band); T016 cancelled.

## Chart

![No-loss gate equity curves](images/orca-race-case.png)

No wallet keys or `.env` files are included.
