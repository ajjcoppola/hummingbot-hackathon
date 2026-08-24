# Install plan — Hummingbot, Gateway, optional zipline

Do **not** reuse `~/proj/hummingbot` or `~/proj/hummingbot-2024*`. Those trees predate Gateway CLMM / `lp_executor` / v2.16.

## 0. What you are installing

```
[this repo: policy + YAML]
        │
        ▼
[Hummingbot client v2.16+]  --MQTT/API-->  [Gateway]  -->  Solana RPC  -->  Orca Whirlpools
        │
        └── optional: pandas / zipline-reloaded 3.11 venv (offline only)
```

Botcamp runs the **finals** in their Docker with $800. You still need a local stack to (1) prove the controller runs and (2) film the demo.

## 1. Hummingbot + Gateway (Docker, recommended)

Docs: https://hummingbot.org/installation/docker/ and https://hummingbot.org/gateway/

```bash
# sibling of this repo — do not dump the client inside hummingbot-hackathon
mkdir -p ~/proj/hummingbot-v216 && cd ~/proj/hummingbot-v216
git clone https://github.com/hummingbot/deploy.git
cd deploy
# follow current README: compose stack that starts hummingbot + gateway
# typical:
cp .env.example .env   # if present
# set GATEWAY / passphrase; never commit .env
```

Verify:

- Hummingbot client comes up
- Gateway swagger on `http://localhost:15888` (dev mode) lists `/connectors/orca/clmm/*`
- `gateway connect solana` → choose **devnet** first

Orca settings live in Gateway `conf/connectors/orca.yml` (`slippagePct`, `maximumHops`).

## 2. Wallet

- Devnet: generate via Gateway; faucet SOL.
- Mainnet (tiny dry run only): a **fresh** Phantom/Solflare wallet, not your primary identity wallet. Fund SOL + USDC. All DEX trades are taxable events.

Never commit seeds. Race capital on Oct 1–2 is **Botcamp-custodied $800** — you do not deposit that yourself.

## 3. Drop in this strategy

From this repo, after the v2.16 client exists:

```bash
# controller
mkdir -p ~/proj/hummingbot-v216/hummingbot/controllers/generic/orca_tight_range
cp ~/proj/hummingbot-hackathon/controllers/orca_tight_range_controller.py \
   ~/proj/hummingbot-v216/hummingbot/controllers/generic/orca_tight_range/
cp -R ~/proj/hummingbot-hackathon/src/orca_tight_range \
   ~/proj/hummingbot-v216/hummingbot/controllers/generic/orca_tight_range/  # or put src on PYTHONPATH

# config
cp ~/proj/hummingbot-hackathon/configs/orca_tight_range.yml \
   ~/proj/hummingbot-v216/hummingbot/conf/controllers/
```

**Runnable fallback if the custom controller import fails:** official `lp_rebalancer` with:

```yaml
controller_name: lp_rebalancer
connector_name: solana-mainnet-beta   # or solana-devnet
lp_provider: orca/clmm
trading_pair: SOL-USDC
pool_address: "<resolved>"
total_amount_quote: 50
side: RANGE
position_width_pct: 1.5
rebalance_threshold_pct: 0.8
autoswap: true
```

That fallback is legal and on-theme. Our controller is the differentiator (skew / exhaustion / rate-limit / stop).

## 4. Resolve `pool_address`

Do not invent an address.

1. Gateway: `POST /gateway/clmm/pools` with `connector=orca`, `chain=solana`
2. Or Orca UI / GeckoTerminal SOL/USDC Whirlpool (0.30% tier)
3. Devnet example cited in the Perplexity plan (verify it still exists): `FcrweFY1G9HJAHG5inkGB6pKg1HZ6x9UC2WioAfWrGkR`

Write the chosen address into `configs/orca_tight_range.yml` and `docs/TRIALS_LEDGER.md`.

## 5. Offline research venv (this repo)

```bash
cd ~/proj/hummingbot-hackathon
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
pytest tests/ -q
python research/orca_backtest_zipline.py --out data/last_backtest.json
python research/zipline_to_gateway_bridge.py --from-json data/last_backtest.json --pool-address ""
```

### Optional zipline-reloaded (Python **3.11** only)

```bash
# separate venv — zipline-reloaded does not support 3.12+
conda create -n hb-zipline python=3.11 -y
conda activate hb-zipline
pip install zipline-reloaded pandas exchange-calendars
# ingest a SOL/USDT minute bundle, then call the same decide() from logic.py
```

Zipline stays **offline**. It never talks to Gateway.

## 6. Suggested timeline (maps to `DAY_PLAN.md`)

| When | Install outcome |
|------|-----------------|
| Aug 23–24 | This repo tests green; Botcamp form submitted |
| Aug 24–25 | Docker Hummingbot + Gateway; Solana **devnet** connect |
| Aug 25–27 | First open/close/rebalance on Devnet |
| Aug 27–29 | Tiny mainnet dry run; film Gateway demo |
| Aug 30–31 | Freeze YAML + `strategy.md`; no more param fishing |

## 7. Health checks

| Check | Pass |
|-------|------|
| `pytest tests/ -q` | all green |
| Gateway `/connectors/orca/clmm/pool-info` | JSON, not 5xx |
| Controller log | `RangeOpened` then either `Hold` or a guarded rebalance |
| No file in git named `*.key` / seed |

If Gateway and local Docker disagree, assume missing env, missing wallet, or the 2024 tree — not a strategy bug.
