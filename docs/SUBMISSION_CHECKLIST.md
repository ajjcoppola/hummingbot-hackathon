# Submission checklist

Deadline of record: **Mon 2026-08-31** (code freeze). Registration also stays open through that date. Do not wait.

## Portal

- [ ] Botcamp account exists
- [ ] Registered on [Agent Builders Cup](https://www.botcamp.xyz/hackathons/agent-builders-cup-1)
- [ ] Applied to **Orca** (rank 1)
- [ ] Optional: also applied to **Meteora** (same stack)
- [ ] Strategy created; fields pasted from `submission/APPLICATION.md`
- [ ] Code files uploaded (controller, backtest, bridge, INSTALL_PLAN, strategy.md)
- [ ] Video URL attached
- [ ] Entry shows as submitted, not only draft
- [ ] Discord `#hackathon` joined

## Repo

- [ ] `python3 -m pytest tests/ -q` is green
- [ ] `pool_address` still empty until you resolve it (do not invent one)
- [ ] No secrets in git (`.env`, wallet keys)
- [ ] Public repo or zip matches what you uploaded

## Build window (after the form is in)

- [ ] Fresh Hummingbot **v2.16+** + Gateway (not the 2024 local clones)
- [ ] Solana **devnet** wallet funded
- [ ] One successful open → close → reopen on a Devnet pool
- [ ] Paper / tiny mainnet dry run logged in `TRIALS_LEDGER.md`
- [ ] Demo video updated with a live Gateway clip
- [ ] `strategy.md` matches the frozen YAML
