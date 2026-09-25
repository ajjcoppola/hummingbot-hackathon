# Install plan — Condor + Gateway Docker

You **can** use Condor for this project. Use it as the **control plane**: start Gateway, attach a Solana wallet, inspect `/lp`, run a bot, film the demo.

Do **not** let the LLM place or cancel LP. Policy stays in `src/orca_tight_range/logic.py`. Execution stays Hummingbot `LPExecutor` + Gateway `orca/clmm`. That matches official rule 05 (unattended race) and the Botcamp split: probabilistic layer reasons, deterministic layer trades.

Do **not** reuse `~/proj/hummingbot` or `~/proj/hummingbot-2024`*. Those trees predate Gateway CLMM / `lp_executor` / v2.16.

Official docs:

- Condor install: [https://condor.hummingbot.org/getting-started/installing](https://condor.hummingbot.org/getting-started/installing)
- Condor quickstart: [https://hummingbot.org/installation/condor/](https://hummingbot.org/installation/condor/)
- Gateway via API: [https://hummingbot.org/gateway/installation/](https://hummingbot.org/gateway/installation/) (Condor path: no standalone Gateway clone)
- Start Gateway: `POST /gateway/start` → [https://condor.hummingbot.org/api-reference/gateway/start-gateway](https://condor.hummingbot.org/api-reference/gateway/start-gateway)



## 0. What you are installing

```
[this repo: policy + YAML]
        │
        ▼
 Condor (Telegram + /web)     <-- you talk here
        │
        ▼
 Hummingbot API :8000         <-- Docker (API + Postgres + EMQX)
        │
        ▼
 Gateway :15888               <-- Docker image hummingbot/gateway:latest
        │                     <-- started by the API, not by a second compose you invent
        ▼
 Solana RPC  -->  Orca Whirlpools
```

Botcamp runs the **finals** in their Docker with $800. This stack is so you can (1) prove the controller / `/lp` loop and (2) film the demo.

Local laptop: skip Tailscale (`n` when asked). Enable Tailscale only if the API will sit on a VPS.

## 1. Prerequisites (Mac)

- Docker Desktop **running** (`docker info` works)
- Telegram account
- 8 GB RAM recommended (4 GB is the documented minimum)

Create a Telegram bot **before** you run the installer:

1. [@BotFather](https://t.me/botfather) → `/newbot` → copy the token
2. [@userinfobot](https://t.me/userinfobot) → `/start` → copy your numeric user id



## 2. Condor + Hummingbot API (one installer)

Sibling of this repo — do not dump Condor inside `hummingbot-hackathon`.

```bash
mkdir -p ~/proj/hummingbot-v216
cd ~/proj/hummingbot-v216

# empty directory only
curl -fsSL https://raw.githubusercontent.com/hummingbot/deploy/main/setup.sh | bash
```

When prompted:


| Prompt                                         | Answer                 |
| ---------------------------------------------- | ---------------------- |
| Telegram bot token                             | from BotFather         |
| Telegram user id                               | from userinfobot       |
| Configure / launch Hummingbot API with Docker? | **yes** (same machine) |
| Tailscale?                                     | **n** on this laptop   |


After it finishes you should have siblings:

```
~/proj/hummingbot-v216/condor/
~/proj/hummingbot-v216/hummingbot-api/
```

Condor runs in tmux session `condor`. API runs in Docker.

```bash
tmux attach -t condor          # logs; detach: Ctrl+B then D
cd ~/proj/hummingbot-v216/hummingbot-api
docker compose ps
```

You want the API container healthy and port **8000** listening.

### Verify Condor + API

1. Open your Telegram bot → `/start`
2. Admins should see **Condor is online and ready.**
3. `/servers` should list the local API (`localhost:8000`)
4. Browser: [http://localhost:8000/docs](http://localhost:8000/docs)

```bash
# replace USER/PASS with hummingbot-api/.env values (often admin/admin on a fresh local box)
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:8000/docs
# expect 200
```

Never commit `condor/.env` or `hummingbot-api/.env`.

## 3. Start the Gateway Docker (via the API)

If you used the Condor Quickstart, **do not** clone Gateway yourself. The API starts `hummingbot/gateway:latest`.

**Telegram (preferred tomorrow):**

`/gateway` → Start Gateway → development mode → passphrase (pick one; remember it; not `admin` if this box is shared)

**Or curl:**

```bash
curl -u USER:PASS -X POST http://localhost:8000/gateway/start \
  -H "Content-Type: application/json" \
  -d '{
    "passphrase": "YOUR_GATEWAY_PASSPHRASE",
    "image": "hummingbot/gateway:latest",
    "port": 15888,
    "dev_mode": true
  }'
```

`dev_mode: true` = HTTP on :15888, Swagger at [http://localhost:15888/docs](http://localhost:15888/docs). Fine for local Devnet. Do not expose 15888 or 8000 to the public internet.

```bash
docker ps --format '{{.Names}}\t{{.Image}}\t{{.Ports}}'
curl -sS -o /dev/null -w "%{http_code}\n" http://127.0.0.1:15888/docs
curl -u USER:PASS http://localhost:8000/gateway/status
```

Pass when Gateway docs return 200 and `/gateway/status` is healthy. Orca CLMM must appear (Swagger: `/connectors/orca/clmm/*` or Condor `/lp` pool list).

### Fallback: standalone Gateway compose

Only if `POST /gateway/start` fails. In `~/proj/hummingbot-v216` (still not this repo):

```yaml
# docker-compose.gateway.yml — local only
services:
  gateway:
    restart: always
    container_name: gateway
    image: hummingbot/gateway:latest
    ports:
      - "15888:15888"
    volumes:
      - "./gateway-files/conf:/home/gateway/conf"
      - "./gateway-files/logs:/home/gateway/logs"
      - "./certs:/home/gateway/certs"
    environment:
      - GATEWAY_PASSPHRASE=YOUR_GATEWAY_PASSPHRASE
      - DEV=true
```

```bash
docker compose -f docker-compose.gateway.yml up -d
```

Then point Condor `/gateway` at `http://localhost:15888`.

## 4. Wallet (Solana, Devnet first)

Devnet is **not** on the Gateway Configuration landing page. That screen only shows Online / Running. Devnet is a **network toggle after you add a wallet**, or under **🌍 Networks**.

Condor does **not** generate a Solana key. It only **imports** a private key. Same key works on Devnet and Mainnet; the network switch is what changes.


| When               | Wallet                                                                    | Fund                                                          |
| ------------------ | ------------------------------------------------------------------------- | ------------------------------------------------------------- |
| This week          | New throwaway Phantom/Solflare (or `solana-keygen`) imported into Gateway | [Solana faucet](https://faucet.solana.com/) SOL on **Devnet** |
| Later tiny mainnet | Same or a second throwaway wallet                                         | Small SOL + USDC from Kraken (Solana network)                 |
| Oct 1–2 finals     | None of yours                                                             | Botcamp-custodied $800                                        |




### Create a throwaway key (do this on your phone/laptop, not in chat)

1. Install [Phatom](https://phantom.app/) or [Solflare](https://solflare.com/).
2. Create a **new** wallet. Do not use your daily identity wallet.
3. Export the **private key** (Phantom: Settings → Security & Privacy → Export Private Key). You want the **base58** string, not a 12-word seed phrase dumped into Telegram as twelve words if you can avoid it — private key is what Gateway asks for.
4. CLI alternative: `solana-keygen new --no-bip39-passphrase --outfile ~/hb-devnet.json` then convert/export to base58, or import that JSON in a wallet and export the private key.

Keep the key in a password manager. Never commit it. Telegram will delete the message after you paste it into Condor, but treat the paste as sensitive.

### Import into Condor (exact taps)

From the screen you have (`Gateway is running. Configure DEX settings…`):

1. Tap **🔑 Wallets** (not Networks yet if you have no wallet).
2. **➕ Add Wallet** → **Solana**.
3. Paste the private key as a Telegram message. Condor forwards it to Gateway and deletes the message.
4. On **Select Networks**, enable **Solana Devnet** (`✅`) and turn **Solana Mainnet Beta** off (`⬜`). Tap **✓ Done**.

To confirm Devnet exists even before a wallet: from Gateway Configuration tap **🌍 Networks**. You should see `solana-devnet` in the list (default is often `✅ solana-mainnet-beta`). Open `solana-devnet` if you need to check the RPC URL.

Then faucet: switch Phantom to **Devnet**, copy the **public** address Gateway showed after import, request SOL at [https://faucet.solana.com/](https://faucet.solana.com/)

Never commit seeds. All **mainnet** DEX trades are taxable.

Do not open an LP until the wallet shows on **devnet** and faucet SOL has landed. Race YAML still uses `solana-mainnet-beta` later.

## 5. First Condor runs (the actual journey)

Do these in order. Stop when the day’s outcome is true.

### A. Stack smoke (Monday)

- `/start` works
- `/servers` Online
- `/gateway` Running, Solana wallet listed, **devnet**
- [http://localhost:15888/docs](http://localhost:15888/docs) loads



### B. Pool, not a trade (Monday)

`/lp` → list Orca Whirlpools → SOL/USDC.

Or:

```bash
curl -u USER:PASS -X POST http://localhost:8000/gateway/clmm/pools \
  -H "Content-Type: application/json" \
  -d '{
    "chain": "solana",
    "network": "devnet",
    "connector": "orca",
    "token_a": "SOL",
    "token_b": "USDC"
  }'
```

Copy a real `pool_address` into `configs/orca_tight_range.yml` (mainnet race) or `configs/lp_rebalancer_devnet.yml` (Devnet smoke) and a row in `docs/TRIALS_LEDGER.md`. Do not invent an address.

Verified Devnet SOL–devUSDC Whirlpool (~0.20%): `3KBZiL2g8C7tiJ32hTv5v3KM7aK9htpqTw4cTXz1HvPt`. Do **not** use `FcrweFY1…` (Whirlpools config account, not a pool).

### C. One on-chain loop (Tuesday)

Tiny Devnet position via `/lp` **or** official `lp_rebalancer` (below). Goal is tx hashes, not alpha:

1. Open a tight range (±1.5%)
2. Wait or nudge until out of range
3. Close
4. Reopen a new tight band

Log signatures in `docs/TRIALS_LEDGER.md`.

`/lp` by hand is a **smoke test**. The race artifact is still the V2 controller (or `lp_rebalancer` fallback) so Botcamp can run it unattended.

### D. Run the strategy as a bot (Wednesday)

`/new_bot` + `/executors` (or `/bots`) with this YAML. If the custom controller is not on the bot image yet, freeze the official fallback:

```yaml
# see configs/lp_rebalancer_devnet.yml
controller_name: lp_rebalancer
connector_name: solana-devnet
lp_provider: orca/clmm
trading_pair: SOL-devUSDC
pool_address: "3KBZiL2g8C7tiJ32hTv5v3KM7aK9htpqTw4cTXz1HvPt"
total_amount_quote: 20
side: RANGE
position_width_pct: 1.5
position_offset_pct: -0.01
rebalance_threshold_pct: 0.8
autoswap: true
```

Drop-in of our controller (when the bot container can import it):

```bash
# paths depend on how hummingbot-api mounts controllers — confirm on the box
# typical: copy into the bot instance conf/controllers and a controllers volume
cp ~/proj/hummingbot-hackathon/controllers/orca_tight_range_controller.py \
   # → the running bot's controllers/generic/
cp ~/proj/hummingbot-hackathon/configs/orca_tight_range.yml \
   # → the running bot's conf/controllers/
```

A running official `lp_rebalancer` beats an unfinished unique controller.

### E. Condor Agent (optional, after the loop works)

`/agent` may wrap the same controller for the application “Agent” tag: journal, Telegram alerts, `/web` dashboard.

In the agent `strategy.md` / risk fields:

- `max_daily_loss_quote` / drawdown aligned with our 15% kill-switch
- Explicit: **LLM must not call place/cancel/open-LP**

That is narration and monitoring, not a second brain on the order path.

## 6. Offline research (this repo, no Docker)

Still useful the night before / if Docker is slow:

```bash
cd ~/proj/hummingbot-hackathon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -q
python research/orca_backtest_zipline.py --out data/last_backtest.json
```

Zipline stays **offline**. Optional 3.11 conda env only if you already use zipline-reloaded.

## 7. Suggested timeline


| When      | Install outcome                                                      |
| --------- | -------------------------------------------------------------------- |
| Aug 23    | This repo committed; Botcamp form when you can                       |
| Aug 24    | Condor + API up; Gateway container started; Devnet wallet            |
| Aug 25    | `/lp` or `lp_rebalancer` open → close → reopen on Devnet             |
| Aug 26    | Custom controller **or** documented fallback running as a bot        |
| Aug 27–29 | Tiny mainnet only if Devnet is boringly green; film `/web` + Gateway |
| Aug 30–31 | Freeze YAML + `submission/strategy.md`                               |




## 8. Health checks


| Check                                   | Pass                                                                                                                                                                     |
| --------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `pytest tests/ -q`                      | all green                                                                                                                                                                |
| `docker compose ps` in `hummingbot-api` | API healthy                                                                                                                                                              |
| `curl` `:8000/docs` and `:15888/docs`   | 200                                                                                                                                                                      |
| Condor `/gateway`                       | Running, Solana, **devnet**                                                                                                                                              |
| `/gateway/clmm/pools` or `/lp`          | real Orca pool, not 5xx                                                                                                                                                  |
| First loop                              | tx hashes in `TRIALS_LEDGER.md`                                                                                                                                          |
| No `*.key` / seed in git                |                                                                                                                                                                          |
| Telegram **Access Pending**             | `ADMIN_USER_ID` was the bot id (digits before `:` in the BotFather token). Set it to your @userinfobot id, make that user `role: admin` in `config.yml`, `make restart`. |


If Condor is up but `/lp` is empty, Gateway is not running or the wallet/network is mainnet-without-funds — not a strategy bug.

If you fall a day behind: skip custom controller, skip `/agent`, keep Condor + Gateway + `lp_rebalancer`.