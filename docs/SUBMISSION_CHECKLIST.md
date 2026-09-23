# Submission checklist

Deadline of record: **Mon 2026-08-31** (code freeze). Registration also stays open through that date. Do not wait.

## Portal

- [ ] Botcamp account exists
- [ ] Registered on [Agent Builders Cup](https://www.botcamp.xyz/hackathons/agent-builders-cup-1)
- [ ] Applied to **Orca** (rank 1)
- [ ] Optional: also applied to **Meteora** (same stack)
- [ ] Strategy created; fields pasted from `submission/APPLICATION.md`
- [ ] Code files uploaded (controller, backtest, bridge, INSTALL_PLAN, strategy.md)
- [x] Video URL attached (`https://www.loom.com/share/687d7c1047534d259b19a4807ea0ef61`)
- [ ] Flowchart images uploaded (`submission/images/*.png`)
- [ ] Entry shows as submitted, not only draft
- [ ] Discord `#hackathon` joined

## Repo

- [ ] `python3 -m pytest tests/ -q` is green
- [x] Devnet `pool_address` resolved in `configs/lp_rebalancer_devnet.yml` (`3KBZiL2…`); mainnet race YAML still filled at freeze
- [ ] No secrets in git (`.env`, wallet keys)
- [ ] Public repo or zip matches what you uploaded

## Build window (after the form is in)

- [ ] Fresh Hummingbot **v2.16+** + Gateway (not the 2024 local clones)
- [x] Solana **devnet** wallet funded (Gateway wallet `2ZuShDjg…`; see TRIALS_LEDGER)
- [x] One successful open → close → reopen on a Devnet pool (T001–T003)
- [x] Paper / tiny mainnet dry run logged in `TRIALS_LEDGER.md` (T009 — $100 SOL-USDC `Czfq3xZZ…`, in-range; reporter running; no finalized race P&L claim)
- [ ] Demo video updated with a live Gateway clip
- [ ] `strategy.md` matches the frozen YAML
