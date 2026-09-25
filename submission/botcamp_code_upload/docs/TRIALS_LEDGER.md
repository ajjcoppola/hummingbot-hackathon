# Trials ledger

One row per parameter change. No silent grid sweeps. Deflate any Sharpe-like claim — this is a 48h fee/IL toy until Gateway fills exist.

| ID | Date | Width % | Trigger % | Skew | Venue | n bars / live hours | Fees | IL | Gas | Net | Decision |
|----|------|---------|-----------|------|-------|---------------------|------|----|-----|-----|----------|
| T000 | 2026-08-23 | 1.5 | 0.8 | 0.6 | synthetic 48h 1m | 2880 | +28.71 | −70.23 | −9.00 | −50.52 | DEFAULT / NO_PROMOTE — toy IL model; 2 deferred flushes; not live |
| T001 | 2026-08-27 | 1.5 | — | — | solana-devnet orca/clmm `3KBZiL2…` | open smoke | — | — | ~0.010 rent | — | PROMOTE path — OPEN tx `5TQ1FcpC…` pos `D9ZtTVDL…` wallet `2ZuShDjg…` (~0.04 SOL + ~0.51 devUSDC) |
| T002 | 2026-08-27 | 1.5 | — | — | same | close smoke | 0 | — | rent refunded ~0.010 | — | CLOSE tx `3Sa35Xst…` (liquidity returned) |
| T003 | 2026-08-27 | 1.5 | 0.8 | — | same | reopen smoke | — | — | — | — | REOPEN tx `dDAoNzVe…` pos `EE6hDunE…` (~0.2 SOL + 5 devUSDC). Official `lp_rebalancer` config `orca_tight_devnet` saved; bot deploy blocked by public RPC 429 + $10 drawdown kill — see notes |

### Live ops notes (2026-08-27)

- Gateway default wallet is **`2ZuShDjgEkdiTtEqbSSCzGUhh5kaFqMjhiuC2VPUNXoB`** (holds SOL + devUSDC). Pubkey `GycxG3EF…` still has ~3 SOL and **no** token accounts — not the LP wallet.
- Pool: `3KBZiL2g8C7tiJ32hTv5v3KM7aK9htpqTw4cTXz1HvPt` (SOL–devUSDC, ~0.20%). Pair symbol must be `SOL-devUSDC`.
- Fallback YAML: `configs/lp_rebalancer_devnet.yml`. Patched host controller `hummingbot-api/bots/controllers/generic/lp_rebalancer/lp_rebalancer.py` for Hummingbot wheel drop of `slippage_pct`.
- Next for unattended bot: Helius (or other) RPC key in Gateway `apiKeys.yml`, redeploy with drawdown ≫ $10, and either close the manual position first or accept Gateway `/lp` as the demo clip.
