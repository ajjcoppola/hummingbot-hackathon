# Sherlock — Why no auto close→open (2026-09-24)

## Verdict

The strategy is **not “Condor-broken.”** It is **semantically mismatched + unmanaged**.

1. Live capital sits in an **orphan LP** with **zero running bots** (`status` → `bots: {}`). Nothing can close/reopen.
2. Even with a healthy `lp_rebalancer` bot, **OUT_OF_RANGE ≠ close**. Official controller only auto-closes when price breaches **limit prices** = band bounds × `(1 ± rebalance_threshold_pct/100)`. Your paste (price **117.00**, upper **116.92**, threshold **0.8%**) was OOR but still **~0.85% short** of the close trigger (~**117.86**).

Condor `/lp` is a viewer. Execution is Hummingbot API bot + Gateway. Do **not** replace that with Condor `/agent` LLM LP.

---

## Step 1 — Possible sources (wide net)

| # | Hypothesis |
|---|------------|
| H1 | No bot running after `adopt` → orphan LP, no executor |
| H2 | Official `lp_rebalancer` waits for **limit prices**, not band exit |
| H3 | Docs/`decide()` say “exit band + trigger from center”; live YAML maps that name to a **different** knob |
| H4 | `get_position_info` / Gateway flaky → executor HOLD / FAILED close |
| H5 | Soft/hard restart leaves orphan; redeploy tries second OPEN → FAILED spam |
| H6 | Custom `orca_tight_range` never deployed; stub can’t Stop+Create cleanly |
| H7 | Condor tmux down mistaken for “strategy down” (UI ≠ executor) |

---

## Step 2 — Most likely (ranked)

| Rank | Cause | Evidence |
|------|-------|----------|
| **1** | **No managing bot** | `mainnet_bot_ops.py status` @ 20:53Z: `bots: {}`, one LP `FZf1…` still open |
| **2** | **Limit-price hysteresis** | Host `lp_rebalancer.py` L702–703: *“No action needed - executor will auto-close via limit prices”*; L734–737: `upper_limit = upper * (1 + threshold)`. Paste: 117.00 &lt; ~117.86 |
| **3** | **Policy dual-brain** | `logic.decide()` rebals on center deviation ≥ 0.8% while OOR; race path uses official controller that **ignores** that |

---

## Step 3 — Code path (investigated)

### Official path (what T009 actually runs)

```
YAML lp_rebalancer
  → LPRebalancerController.determine_executor_actions()
      active executor? → return []   # wait for limit-price auto-close
      no executor?     → maybe CreateExecutorAction (autoswap → open)
  → LPExecutor (Gateway orca/clmm open/close)
```

Critical lines (`hummingbot-api/.../lp_rebalancer/lp_rebalancer.py`):

- Docstring: threshold is **% beyond position bounds**, not “deviation from center”.
- Active executor branch: **no** OOR close logic — only waits.
- `_create_executor_config`: sets `upper_limit_price` / `lower_limit_price` from `rebalance_threshold_pct`.

### Math on your Condor paste

| Quantity | Value |
|----------|-------|
| Band | [115.20, 116.92] |
| Spot | 117.003 |
| In band? | **No** (OOR) |
| Close if `threshold=0.8%` | spot ≥ 116.92 × 1.008 ≈ **117.86** |
| Would official close? | **No** |
| Would `decide()` rebal? | **Yes** (dev from center ≈ 0.81% ≥ 0.8%) |

Holdings `0 SOL / ~99 USDC` = classic **above-range** single-sided inventory — expected while OOR and **before** close.

### Custom path (not live)

`controllers/orca_tight_range_controller.py` calls `decide()` but:

- Not the deployed `controller_name`
- On REBALANCE it `CreateExecutorAction` only — no explicit stop/close of prior LP
- `_position` is in-memory only; restart = amnesia

### Condor

Keep as **dashboard + ops shell**. Dropping Condor does not fix rebalance. LLM `/agent` must stay non-executing.

---

## Step 4 — Analysis

| Layer | Intended | Actual race path | Gap |
|-------|----------|------------------|-----|
| Policy | Close when leave band + filters | Limit-price hysteresis beyond band | **Wrong knob semantics** |
| Execution | One managed LP | Orphan after adopt / failed close | **No executor** |
| Ops | Soft restart “fixes” OOR | Soft restart cannot attach orphan | **Wrong recovery** |
| UI | Condor shows OOR | Operator expects immediate close | **Expectation bug** |

**Not broken:** Gateway can show `position_info` PASS; pool/range math is coherent; Devnet open→close→reopen (T001–T003) proved the stack *can* turn.

**Broken for race goals:** zero rebalances overnight with long OOR stretches; capital unmanaged after adopt; tightening width alone won’t help if close never fires until +0.8% **past** the already-tight band.

---

## Step 5 — Plan to make it work (ordered)

### P0 — Restore a managed loop (today, ~30–60 min)

1. `python3 scripts/mainnet_bot_ops.py status` — confirm orphan vs managed.
2. `adopt --recycle --restart-gateway` — **close** `FZf1…`, deploy **one** `lp_rebalancer`, wait for single OPEN.
3. Start `restart-reporter` + `mainnet_health_watchdog` (Gateway restart on `position_info` fail; alert on OOR — do **not** soft-restart forever hoping for rebal).
4. Ledger row **T010**: “managed after orphan recycle”.

Success: `status` → 1 running bot, 1 LP, `position_info` PASS.

### P1 — Fix close semantics (same day, YAML-only A/B)

Official controller will **not** close at first OOR with `rebalance_threshold_pct: 0.8`.

| Trial | Change | Intent |
|-------|--------|--------|
| T011 | `rebalance_threshold_pct: 0.05` (or `0.1`) | Close almost as soon as price leaves band |
| Hold width | keep `position_width_pct: 1.5` | Isolate hysteresis effect |

**Do not** set threshold to invent a second “center trigger” — that knob is **beyond-bounds**, not center deviation.

Success metric (2–4h): ≥1 successful close→open when spot leaves band; `n_rebals ≥ 1`; no FAILED-open spam.

### P2 — Simplify ops surface (keep Condor, shrink script theater)

**Keep:** Condor UI, API, Gateway, one bot, `status` / `adopt` / `adopt --recycle` / reporter / watchdog.

**Stop relying on:** soft-restart as rebalance; hard-restart with open LP; LLM agent LP; multi-bot same wallet.

Optional watchdog upgrade: if `in_range=false` **and** `spot > upper*(1+threshold)` for N polls **and** state still not CLOSING → page human / recycle (detects stuck executor).

### P3 — Only if P1 fails: promote custom controller (1–2 days)

Wire `orca_tight_range` into hummingbot-api bots tree **only if** YAML hysteresis cannot meet race volume:

1. On `Action.REBALANCE`: StopExecutor / close LP **then** Create (not Create alone).
2. Sync `_position` from Gateway `positions_owned` on start (no orphan amnesia).
3. Devnet proof of close→open under OOR, then mainnet $100.

Until then: **one brain** = official `lp_rebalancer` YAML. Keep `logic.py` as research/spec; don’t run both.

### P4 — After loop proven: param refine for Cup

Width 1.5 → 1.0 (volume), size toward $800, pool re-screen — **after** T011 shows rebalances &gt; 0.

---

## Step 6 — Diagnostic logging (temporary)

Add (or log via reporter) per poll:

- `spot`, `lower`, `upper`, `upper_limit`, `lower_limit`, `in_range`, `past_close_limit`, `bot_running`, `executor_state`, `position_address`

Remove after T011 proves ≥1 rebal — ask before deleting.

---

## Recommendation (direct)

| Question | Answer |
|----------|--------|
| Abandon Condor? | **No** — keep as UI; execution stays API+Gateway+bot |
| Simplify? | **Yes** — one managed bot; recycle orphans; stop soft-restart theater |
| Why no close on your paste? | OOR but **inside** 0.8% beyond-upper hysteresis **and** (after adopt) **no bot** |
| Next command | `python3 scripts/mainnet_bot_ops.py adopt --recycle --restart-gateway` then T011 threshold tighten |

---

## Live snapshot (agent check 2026-09-24 20:53Z)

- Gateway PASS; portfolio free USDC ~10 (rest in LP)
- LP `FZf1…` **in_range true** again (price bounced to ~116.91)
- **`bots: {}`** — still unmanaged
