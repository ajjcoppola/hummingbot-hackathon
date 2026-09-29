# Sherlock session — race strategy implementation (2026-09-28)

## Plan

Race entry = **new** `orca_dynamic_farmer` controller (hourly SOL-USDC tier rank + 16%/0.5 band + hysteresis switches). Official `lp_rebalancer_race_800` = fallback if T017 fails. T016 untouched. Entry freeze 2026-10-01; race 2026-10-06.

## What shipped

| Piece | Path |
| --- | --- |
| Ranker | `src/orca_tight_range/pool_rank.py` + `tests/test_pool_rank.py` |
| Pure decision layer | `src/orca_tight_range/dynamic_farmer.py` |
| ML shadow | `src/orca_tight_range/ml_intensity.py` + tests |
| Controller | `controllers/orca_dynamic_farmer_controller.py` |
| Configs | `configs/orca_dynamic_farmer_{800,100}.yml`, `configs/lp_rebalancer_race_800.yml` |
| Offline harness | `tests/test_dynamic_farmer_harness.py` |
| Snapshot collector | `research/pool_snapshot_collector.py` + LaunchAgent plist |
| R003 | `research/r003_multi_pool_replay.py` → `data/r003_grid_20260928.json` |
| T017 gate | `scripts/t017_prep.py` (WAIT until T016 ends) |
| Watchdog | `pool_switch` field + alert if >3/48h |

## Critical correction (R003)

R002 `pool_screen` used `tokens=SOL,USDC` (**OR**). “Higher intensity SOL-USDC” addresses were other pairs (SOL-PUMP, ZEC-USDC, …). True `tokensBothOf` universe: only **Czfq3xZZ…** clears TVL ≥ $500k. Dynamic farmer correctly holds Czfq under hard filters; infrastructure still ready if a qualifying tier appears.

## Verification

- `pytest` pool_rank + harness + ml_intensity: pass
- Snapshot LaunchAgent `com.hummingbot.pool-snapshots` installed; writes `data/pool_snapshots.jsonl`
- R003 switcher holdout: Czfq only, 0 switches, edge ~+$9 (constant-TVL caveat)
- `t017_prep.py`: STATUS=WAIT while T016 clock runs

## Manual follow-ups

1. Post `docs/DISCORD_VOLUME_QUESTION.md` in Discord `#hackathon`; paste answer into `docs/RULES_DIGEST.md`.
2. After T016 ends (2026-09-30 18:26Z): `python3 scripts/t017_prep.py --check` then deploy `configs/orca_dynamic_farmer_100.yml`.
3. Do not tune code after Oct 1 freeze.
