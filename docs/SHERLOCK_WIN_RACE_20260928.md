# Sherlock — Win-race plan (2026-09-28)

Score target: **Volume 40% / P&L 40% / HBOT Vote 20%** on Botcamp’s **$800**, unattended 48h, Orca only.

## Verdict

**T015 cannot be saved as a clean 48h.** Do not keep the clock.

The live bot `orca_tight_mainnet_smoke-20260928-150028` has **zero LP** and is looping a dust Jupiter sell. The watchdog logs that state as **`healthy`**. Any real fix restarts the process, so “upgrade without stopping the eval” is not available. Restart as **T016** with the same width **1.0** / threshold **0.05**. Tightening to 0.75% and personal $800 funding wait until T016 is clean.

Volume is won by **uptime inside the band**, then by notional. A flat bot scores 0 volume and 0 fee P&L no matter the width.

---

## Step 1 — Possible sources

| # | Hypothesis |
|---|------------|
| H1 | Quote deficit of ~$0.000074 triggers `SELL` that quantizes to **0 SOL**; Jupiter `NO_ROUTE_FOUND` retries forever and never opens |
| H2 | Watchdog treats **running bot + 0 positions** as healthy, so nothing recycles the flat state |
| H3 | Prior OPEN in this container failed (`TRANSACTION_FAILED`, blockhash expiry, then “token amount too small”), so inventory never returned to a managed LP |
| H4 | Helius **429** on `position_info` made the executor close a real LP (`EqfbWNWy…`) and then fail the reopen |
| H5 | `position_offset_pct: -0.01` plus a one-sided close leaves a quote target of `99.000100` against `99.000026` USDC |
| H6 | Width 1.0 is too wide for Cup volume (user’s prior belief) |
| H7 | Submission text (width 1.5 / trigger 0.8 / Aug 31 freeze) will lose the HBOT vote even if the bot runs |

## Step 2 — Most likely

| Rank | Cause | Why this one |
|------|--------|----------------|
| **1** | **Dust autoswap gate** | Log at 17:21Z: `deficit quote=0.000074` → `SELL 0.000001` → Gateway `SELL 0.000000` → `NO_ROUTE_FOUND` → `Will retry on next cycle` |
| **2** | **Watchdog blind to flat** | `watchdog.jsonl` 17:10–17:22Z: `n_positions: 0`, `action: none`, `detail: healthy` every poll |
| **3** | **T015 already restarted once** | Ledger clock ~2026-09-27 17:28Z / bot `…172722`. Live container is `…150028` from 15:00Z. Reporter meta `started` is `2026-09-28T15:02:31Z`. A third restart does not preserve an unattended 48h |

H6 is real for the **race**, and wrong for **this rescue**. Width changes need a new OPEN. Do that only after a 48h that stays in-range.

---

## Step 3 — Code path

Official controller (bind-mounted, not `logic.py`):

`~/proj/hummingbot-v216/hummingbot-api/bots/controllers/generic/lp_rebalancer/lp_rebalancer.py`

```379:394:hummingbot-api/bots/controllers/generic/lp_rebalancer/lp_rebalancer.py
elif quote_deficit > 0 and base_deficit <= 0:
    swap_amount = (quote_deficit / current_price) * buffer_multiplier
    if base_balance >= swap_amount * Decimal("1.02"):
        # SELL swap_amount — no minimum notional
```

Any `quote_deficit > 0` sells. At SOL ~$118, a **$0.000074** deficit is ~**6e-7 SOL**. Gateway sends **0**. Jupiter has no route. The controller never reaches “no swap needed, balances sufficient” (around line 672), so it never opens.

Container evidence (2026-09-28, bot `…150028`):

| Time (UTC) | What happened |
|------------|----------------|
| 15:00:35 | Autoswap BUY 0.36 SOL succeeded |
| 15:00:43 | OPEN `TRANSACTION_FAILED` (landed, unknown error) |
| 15:06–15:09 | OPEN blockhash expired, resubmit |
| 15:17:34 | Close `EqfbWNWy…` confirmed; returned **0.657 SOL, 0 USDC** |
| 15:17:39 | Next OPEN `side=SELL` quote **$1.00** → `Token amount is too small` |
| 17:21+ | Dust SELL loop. Wallet ~**99.00 USDC + 0.179 SOL**, **0 positions** |

Watchdog gap (`research/mainnet_health_watchdog.py`):

- `len(running)==0 and len(pos)==0` → `alert_flat_no_bot` (line 214)
- `len(pos)==1` and (no bot or past limit) → `adopt --recycle` (line 217)
- **`len(running)==1 and len(pos)==0` falls through to `detail = "healthy"`** (line 288)

`adopt --recycle` also refuses when there is no LP (`scripts/mainnet_bot_ops.py`: “no LP to adopt — use hard-restart”). The flat+running case needs **hard-restart**, and hard-restart without the dust floor recreates this loop.

---

## Step 4 — Analysis

| Pillar | What T015 is doing now | What a winnable entry needs |
|--------|------------------------|-----------------------------|
| Volume 40% | 0 since ~15:17Z. Capital is free USDC, not in the whirlpool | LP open on `Czfq3xZZ…` for the whole 48h. Rebals only when spot crosses limit prices |
| P&L 40% | Dust swaps fail (no fill). Failed opens still burn attempts / blockhash | Skip sub-route swaps. Stay in range. Gas only on real rebals |
| HBOT Vote 20% | `submission/strategy.md` still says width **1.5%**, trigger **0.8%**, freeze **2026-08-31**, live status **T009** | Honest public story: official `lp_rebalancer`, width 1.0, threshold 0.05, HB 2.17, demo of close→open |

**Do not do these in the rescue restart**

| Idea | Why not now |
|------|-------------|
| Width 1.0 → 0.75 or 0.5 | More rebals only if the bot stays up. R001 0.5% is synthetic and net-negative on the toy model. New trial after T016 |
| Personal $800 (`configs/lp_rebalancer_mainnet_800.yml`) | Race book is Botcamp’s $800. Self-fund stays blocked until a clean 48h (`docs/UNSANCTIONED_800.md`) |
| Patch `src/orca_tight_range/logic.py` | Live path does not call `decide()`. A second policy forks the race bot |
| Soft-restart the current container | Reloads the same dust loop. No LP to adopt |

**Clock math.** T015’s useful window was ~21.6h (reporter), then a new container at 15:00Z, then flat. Finals start **2026-10-01**. A T016 clock started **2026-09-28 ~18:00Z** ends **2026-09-30 ~18:00Z**, inside the refine window and before finals. That is the last clean 48h that still fits.

---

## Step 5 — Execution plan (T016)

Order matters. Patch first, then restart, then prove an OPEN before calling it the new clock.

### A. Dust floor (controller, hummingbot-v216 mount)

In `_get_autoswap_order` (the deficit branch around lines 355–407), if the only deficit is below a minimum quote notional, return `None` (same as “balances sufficient”) instead of building an `OrderExecutorConfig`.

- Floor: **0.05 USDC** equivalent (covers the $0.000074 case and Jupiter’s zero-amount reject; still swaps a real $1+ inventory gap).
- Apply to quote-deficit SELL, base-deficit BUY, and the both-deficit warning when the **sum** is under the floor.
- Do not change width, threshold, pool, or `decide()`.
- This file is bind-mounted at `/home/hummingbot/controllers`. The running process will not see it until the container is replaced.

### B. Watchdog: flat + running → hard-restart

In `research/mainnet_health_watchdog.py`, before the `healthy` branch:

- If exactly one bot is running and `n_positions == 0` for **3 polls** (~6 min) → `hard-restart` (not `adopt --recycle`).
- Cooldown so a slow OPEN is not killed mid-submit (reuse `recycle_cooldown_s` or a dedicated `flat_restart_cooldown_s`, start at 20 min).
- Log action `flat_hard_restart`, not `healthy`.
- Keep orphan / past-limit `adopt --recycle` as it is.

### C. Restart the clock (this stops T015)

1. Ledger: mark **T015 FAIL** — interrupted at container `…150028`; flat dust loop from ~15:17Z; watchdog false healthy. Keep the 21.6h tearsheet as evidence, not as a pass.
2. `python3 scripts/mainnet_bot_ops.py hard-restart` with the **existing** smoke YAML (width 1.0, threshold 0.05, quote 100). No width edit.
3. Wait until status shows **1 in-range LP**. If OPEN fails “too small” or dust-sells again, stop and read logs before a second deploy.
4. New reporter run-id `T016_mainnet_100_hb217_20260928`. New ledger row. LaunchAgent reporter id updated. Watchdog left running with the flat branch.

### D. Submission honesty (no LP effect; do after OPEN is confirmed)

- `submission/strategy.md`: live path is official `lp_rebalancer` at width **1.0** / threshold **0.05**; drop the Aug 31 freeze; live status = T016 in progress, no P&L claim.
- `submission/FORM_PASTE.md`: same params (it still says 1.5 / 0.8).
- Vote package stays: public repo, strategy.md, Condor `/lp` demo of a real rebalance. LLM does not place LP.

### E. After T016, only if it stays in-range ~48h

| Next | When |
|------|------|
| Width **0.75** as T017 | T016 finished with no multi-hour flat and fees − gas ≥ 0 on the tearsheet |
| Botcamp **$800** config | Copy smoke YAML quote 800 onto **their** wallet at finals, not this wallet |
| Personal $800 | Still blocked |

### Diagnostics to leave in until T016’s first successful OPEN

- Existing autoswap deficit log line (already there).
- Watchdog `flat_hard_restart` jsonl row.
- No extra print spam in the controller beyond the one “skip dust deficit” info line.

### Related code with the same hole

- `scripts/mainnet_bot_ops.py` `adopt` without `--recycle` does not deploy when flat; only hard-restart does.
- Gateway restart on `position_info` 429 does not clear a dust loop.
- `configs/lp_rebalancer_mainnet_800.yml` has the same `autoswap: true` and will hit the same floor once quote is 800; the controller patch covers it.

## Step 6 — Cleanup

After T016 shows one in-range LP and one full watchdog poll that is actually healthy (`n_positions == 1`), ask before removing the “skip dust deficit” info log.

---

## What I am not doing in this write-up

No hard-restart, no YAML width change, no $800 fund, no controller edit yet. Those start when this plan is approved, beginning with **A → B → C**.
