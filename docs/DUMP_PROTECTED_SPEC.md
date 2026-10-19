# Dump-protected LP v1 (S002-style)

Same Czfq **16% / 0.5** race shell with a hard risk budget: cash sleeve + USDC-heavy open + −3% equity kill. No arb swarm. No CEX/perp hedge in the executable stack (Orca / Solana only).

## Locked knobs

| Knob | Value | Notes |
|------|-------|-------|
| Pool | `Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE` | Verified; never invent |
| Width / thr | 16.0 / 0.5 | Race shell unchanged |
| Book | ~$150–160 wallet | Post-Cup flat |
| Cash sleeve | **40%** of book in USDC, never deposited | Ops discipline — not a YAML field |
| LP notional | **60%** → `total_amount_quote: 90` | Leaves ~$60+ sleeve on a ~$150 book |
| Side / offset | `BUY` / `position_offset_pct: -4.0` | See verification below |
| Equity kill | Flatten if `equity ≤ open_equity × 0.97` | `scripts/equity_kill.py` |
| Autoswap | true | Needed for in-range BUY mix |

Config file: [`configs/lp_rebalancer_dump_protected_120.yml`](../configs/lp_rebalancer_dump_protected_120.yml).

## Sleeve math (example ~$150 book)

| Sleeve | USD | Where |
|--------|-----|-------|
| Cash USDC | 60 (40%) | Wallet; do not raise `total_amount_quote` to absorb it |
| LP quote | 90 (60%) | `total_amount_quote` |
| SOL dust | rent/gas only | Keep ~0.05–0.1 SOL free outside the LP target |

If wallet equity changes before deploy, keep the **40/60 split**:  
`total_amount_quote ≈ 0.6 × deployable_equity` (round down; leave gas).

## Offset verification (Hummingbot `lp_rebalancer`)

Verified against `hummingbot-api` controller `lp_rebalancer.py` (HB 2.16/2.17 tree):

1. **`side: RANGE` ignores `position_offset_pct`** for both price bounds and amounts (centered 50/50). Using RANGE + non-zero offset is a no-op — do not ship that for dump-protected.
2. **Negative `position_offset_pct` = in-range** (needs both tokens; autoswap converts). Positive = out-of-range single-sided.
3. For **`side: BUY`** with negative offset:
   - `upper = spot × (1 − offset/100)` with `offset < 0` ⇒ upper **above** spot
   - `lower = upper × (1 − width/100)`
   - Quote share ≈ `(spot − lower) / (upper − lower)` → spot sits in the **upper** portion of the band ⇒ **USDC-heavy**
4. Chosen default **`position_offset_pct: -4.0`** with width 16:
   - upper ≈ `1.04 × spot`, lower ≈ `0.8736 × spot`
   - quote fraction ≈ **0.76** at open (upper-third / USDC-heavy)
5. Allowed range for v1 experiments: **−3.0 to −5.0** (must satisfy `|offset| ≤ width`).

Checklist before live deploy:

- [ ] YAML has `side: BUY` (not RANGE)
- [ ] `position_offset_pct` in [−5, −3]
- [ ] `total_amount_quote` ≈ 60% of wallet equity; USDC free ≥ sleeve
- [ ] Equity-kill LaunchAgent loaded with matching `EQUITY_KILL_OPEN` or auto-baseline
- [ ] Watchdog / reporter run id set for S002 (ledger row)

## −3% equity kill

- **Trigger:** `equity_usd ≤ open_equity_usd × 0.97`
- **Action:** stop matching bots, close **all** Czfq positions (loop until flat), leave wallet in USDC (+ SOL dust). No redeploy.
- **Why companion script:** keep Cup/mainnet watchdog focused on recycle/OOR; kill is a hard risk rail.
- **Confirm:** on-chain `positions_owned` empty after close (Gateway 400 alone is not proof — Cup orphan lesson).

State + logs: `data/equity_kill/`.

## Out of scope (v1)

- Arb / inventory swarm
- Hyperliquid / CEX / Derive hedges
- Changing width/threshold away from 16 / 0.5 without a new ledger row

## Trial wiring

Ledger id **S002** = PREP until a live window starts. Blog: [`docs/blog/czfq-dump-protected-postmortem.md`](blog/czfq-dump-protected-postmortem.md).
