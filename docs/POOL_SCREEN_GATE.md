# Pool screen gate — research BEFORE joining

**Venue:** Orca Whirlpools on **solana-mainnet-beta** only. Devnet is harness smoke, not a fee market. Meteora / Raydium / CEXes are out of scope for this repo.

**Rule:** Do not put a `pool_address` into a live YAML or deploy until this gate is **PASS** and a row exists in [`TRIALS_LEDGER.md`](TRIALS_LEDGER.md).

---

## 1. Screen (automated)

```bash
python3 research/orca_pool_screener.py
# SOL-USDC focus:
python3 research/orca_pool_screener.py --tokens-both SOL,USDC
```

Writes `data/pool_screens/YYYYMMDD_HHMM.json` and prints PASS/FAIL plus chart URLs.

Default thresholds:

| Filter | Default |
|--------|---------|
| `min_vol_24h` | $5,000,000 |
| `min_tvl` | $1,000,000 |
| `hasWarning` | must be false |

---

## 2. PASS checklist (all required)

| # | Check | Evidence |
|---|--------|----------|
| 1 | Mainnet Orca whirlpool (not Devnet) | Screener address; network `solana-mainnet-beta` |
| 2 | 24h volume ≥ threshold | Screener `volume_24h` |
| 3 | TVL ≥ threshold | Screener `tvl_usdc` |
| 4 | Fee tier understood | `fee_pct` — ultra-low fee = more flow, thinner fee/$; mid/high fee = fatter fee/$ if still liquid |
| 5 | Charts show real action | Open GeckoTerminal / DexScreener / Orca links from screener — continuous candles, non-flat 24h volume |
| 6 | Gateway resolves pool | `GET /gateway/clmm/pool-info?connector=orca&network=solana-mainnet-beta&pool_address=…` via Helius |
| 7 | Ledger row **before** OPEN | New ID in `docs/TRIALS_LEDGER.md` |
| 8 | Wallet funded | `2ZuShDjg…` has SOL gas + deploy quote (e.g. ~100 USDC) on **mainnet** |

**PASS** → may copy address into config by hand and follow [`MAINNET_TOMORROW.md`](MAINNET_TOMORROW.md).  
**FAIL** → do not join; re-screen or change thresholds (ledger the why).

---

## 3. Graphical viewers

For any shortlisted address `POOL`:

- Orca: `https://www.orca.so/pools/POOL`
- GeckoTerminal: `https://www.geckoterminal.com/solana/pools/POOL`
- DexScreener: `https://dexscreener.com/solana/POOL`
- Dune (protocol tops): https://dune.com/orca/orca-top-whirlpools
- Condor: `/lp` → Explore → Orca (network must be **solana-mainnet-beta**)

---

## 4. Known baseline candidate

| Field | Value |
|-------|--------|
| Pair | SOL-USDC |
| Address | `Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE` |
| Config | [`configs/lp_rebalancer_mainnet_smoke.yml`](../configs/lp_rebalancer_mainnet_smoke.yml) |
| Note | Must still **PASS** a fresh screener run on deploy day — do not skip the gate because it was hot yesterday |

---

## 5. Explicit non-goals

- No Devnet volume / P&L claims  
- No inventing `pool_address`  
- No auto-writing screener output into YAML  
- No Meteora/Raydium venue switch  
- No Condor `/agent` LP placement  
- No committing Helius / wallet secrets  
