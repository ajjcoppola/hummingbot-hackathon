# Orca race case — Beta Checkpoint collateral

**One folder for tomorrow’s selection conversation.** Everything below is simulation-honest and key-free.

## Start here (10 minutes)

1. Open **`pdf/orca-race-case.pdf`** — pitch deck with no-loss gate + equity chart.
2. Skim **`pdf/cup-800-sim.pdf`** — PDF render of the Cup money-search canvas.
3. Paste from **`collateral/APPLICATION.md`** into the Botcamp strategy page.
4. Upload code + **`sims/`** (or the whole `submission/orca_race_case/` tree).

## Layout

| Path | Contents |
|------|----------|
| `pdf/` | `orca-race-case.pdf`, `cup-800-sim.pdf`, chart PNG |
| `canvases/` | Cursor `.canvas.tsx` sources (cup-800-sim + prior tearsheets) |
| `sims/` | R002/R003 JSON, no-loss gate, ML shadow status, `SIMULATION_RESULTS.md` |
| `collateral/` | APPLICATION, strategy, page update, ledger, rules, Sherlock log |
| `configs/` | Race YAML (`…_race_800.yml`) + live proof (`…_r003m_100.yml`) |

## Talking points

- **No-go:** tight 1% band → **−$557** in the same sim.
- **Pass:** sit-wide 16% → **+$29 / +$25** train/holdout absolute.
- **Race entry:** 16% / 0.5 holdout **+$24**; executable via official `lp_rebalancer`.
- **Pool:** only Czfq clears TVL gate among true SOL-USDC tiers (R003).
- **Volume:** fees-implied (not our own swaps).
- **Live:** R003m proof running; T016 cancelled.

## Regenerate PDFs

```bash
export MPLCONFIGDIR=$PWD/.mplconfig
# re-run the render script from research or this README’s companion in scripts/
```

No wallet keys or `.env` files are included.
