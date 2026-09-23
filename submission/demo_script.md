# Demo video shot list (2–4 minutes)

Official rule 05: show the agent/controller **running**. Prefer a Gateway Devnet clip. Do not claim mainnet P&L.

## Record this (current stack — 2026-08-27)

### 0. Prep (before you hit record)

- Gateway + Hummingbot API up (`localhost:8000`)
- Optional: Condor Telegram `/lp` or `/web` if you use it for narration
- Browser ready: Solana Explorer **Devnet** for the position tx
- Wallet to show (public only): `2ZuShDjgEkdiTtEqbSSCzGUhh5kaFqMjhiuC2VPUNXoB`
- Live position: `EE6hDunE2qpTATywgudXDLXrUJ1HVg7CWJZmMxKwdaFN`
- Pool: `3KBZiL2g8C7tiJ32hTv5v3KM7aK9htpqTw4cTXz1HvPt` (SOL–devUSDC)

Explorer links (Devnet):

- Position open (T003): https://explorer.solana.com/tx/dDAoNzVebSihR6etP67fw4Lu31KL68fPeP54bQz6TA6CMFMMAH64UpGyrTY91H9V23hRsTdFw34kYyDbRkAjQHj?cluster=devnet
- Prior close (T002): https://explorer.solana.com/tx/3Sa35XstCVCNYpuk2xS82pJeeKgsXbGbHoS5EXxzyVPVwqUB9dqhmTnVhi9GqV6YQG5bT2fhqMeo59wM8H4DjJz7?cluster=devnet
- Prior open (T001): https://explorer.solana.com/tx/5TQ1FcpCbs9fSU2FW7T4G4z8K14WTVn47Wm1cYNeRzDvU444qHhsPwgHePhX8CWEvy68EpGnKPD1m6YsvVwCAYUy?cluster=devnet

### 1. Title (5s)

"Orca Tight-Range Leverage Farmer — Agent Builders Cup — Devnet Gateway demo"

### 2. Intent (15s)

Say out loud:

- Venue: **Orca Whirlpools** on Solana (US-legal; no Gate/Bitget/Binance Global/Hyperliquid/Derive)
- Policy: tight ±1.5% RANGE, recenter when out of band, 15% kill-switch
- Execution: Hummingbot `LPExecutor` + Gateway `orca/clmm`
- LLM does **not** place or cancel LP

### 3. Repo + tests (30s)

```bash
cd ~/proj/hummingbot-hackathon
pwd
git log -1 --oneline
python3 -m pytest tests/ -q
```

Flash `src/orca_tight_range/logic.py` (`decide()`) and `configs/lp_rebalancer_devnet.yml`.

### 4. Live Gateway proof (90–120s) — the important part

In a terminal (or Condor `/lp` if you prefer the UI):

```bash
# show funded Gateway wallet + in-range position
# use your local hummingbot-api basic-auth user:pass (never commit it)
API_AUTH="${HB_API_USER}:${HB_API_PASS}"

curl -sS -u "$API_AUTH" -X POST http://127.0.0.1:8000/portfolio/state \
  -H 'Content-Type: application/json' -d '{}' | python3 -m json.tool

curl -sS -u "$API_AUTH" -X POST http://127.0.0.1:8000/gateway/clmm/positions_owned \
  -H 'Content-Type: application/json' \
  -d '{
    "connector": "orca",
    "network": "solana-devnet",
    "pool_address": "3KBZiL2g8C7tiJ32hTv5v3KM7aK9htpqTw4cTXz1HvPt",
    "wallet_address": "2ZuShDjgEkdiTtEqbSSCzGUhh5kaFqMjhiuC2VPUNXoB"
  }' | python3 -m json.tool
```

On screen, point at:

- `in_range: true`
- bounds ~±1.5% around spot
- `lp_provider` / Orca pool address

Open Explorer Devnet on the three txs (open → close → reopen). Say: "Unattended race path is the same open / out-of-range close / reopen loop."

### 5. Close (10s)

"Code freeze Aug 31. Finals Oct 1–2 on Botcamp-custodied capital. No fabricated live P&L."

### Upload

Loom / YouTube **unlisted** / Drive anyone-with-link → paste into Botcamp **Video Link**.

## Do not say

- Mainnet profit numbers you do not have
- That the Chrome extension wallet is the bot wallet (bot = Gateway `2ZuShD…`)
- That Zipline tuned the live params (skipped for time)
