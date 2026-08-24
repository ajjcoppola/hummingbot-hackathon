# Demo video shot list (2–4 minutes)

Official rule 05 requires a video of the agent or controller **running**. Tonight you can ship a policy + simulator run; replace or append a Gateway clip before Aug 31.

## Tonight (enough to attach a link)

1. Title card: "Orca Tight-Range Leverage Farmer — Agent Builders Cup"
2. `pwd` + `git log` / file tree of this repo
3. Read `submission/strategy.md` on screen (20s)
4. Terminal:

```bash
cd ~/proj/hummingbot-hackathon
python3 -m pytest tests/ -q
python3 research/orca_backtest_zipline.py
```

5. Point at `RangeOpened` / `RebalanceDeferred` / stop-loss in `src/orca_tight_range/logic.py`
6. Close: "Gateway Devnet open/close/rebalance is the remaining build-window work. Code freeze Aug 31."

Upload to Loom / YouTube unlisted / Drive (anyone-with-link). Paste URL into the Botcamp **Video Link** field.

## Before Aug 31 (required for a serious seat)

1. Hummingbot + Gateway up (`docs/INSTALL_PLAN.md`)
2. `gateway connect solana` on **devnet**
3. Resolve a pool address
4. Open a tiny position, show it in-range, force or wait for an out-of-range close, show reopen
5. Show `lphistory` or Gateway position-info
6. Say out loud: unattended 48h, no manual orders

Keep the clip boring and true. Do not claim live mainnet P&L you do not have.
