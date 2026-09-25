# Orca Tight-Range Leverage Farmer

Agent Builders Cup entry for the **Orca** team: an active tight-range Whirlpool LP on SOL/USDC.

This repo is the **application pack + 8-day build guide**. Official rules freeze code at **2026-08-31**. Finals are a 48-hour unattended race on **2026-10-01–02** with **$800 USDC** provided by Botcamp. Scoring is Volume 40% / P&L 40% / HBOT Vote 20%.

Do **not** use the 2024 Hummingbot trees under `~/proj/hummingbot*`. Live work is **Condor + Hummingbot API Docker + Gateway Docker** (v2.16+). Condor may start Gateway, run `/lp`, and host the bot. It must not let the LLM place orders. See [`docs/INSTALL_PLAN.md`](docs/INSTALL_PLAN.md).

## Tonight (get the application in)

1. Open [Agent Builders Cup](https://www.botcamp.xyz/hackathons/agent-builders-cup-1) and register if needed.
2. Apply to **Orca**. Rank Orca first. Optional backup: Meteora (same Solana Gateway path).
3. Create / edit the Botcamp strategy. Paste from [`submission/APPLICATION.md`](submission/APPLICATION.md).
4. Attach this repo (or zip) as **Code Files**:
   - [`controllers/orca_tight_range_controller.py`](controllers/orca_tight_range_controller.py)
   - [`research/orca_backtest_zipline.py`](research/orca_backtest_zipline.py)
   - [`research/zipline_to_gateway_bridge.py`](research/zipline_to_gateway_bridge.py)
   - [`docs/INSTALL_PLAN.md`](docs/INSTALL_PLAN.md)
   - [`submission/strategy.md`](submission/strategy.md)
5. Record a 2–4 min video from [`submission/demo_script.md`](submission/demo_script.md) (tests + strategy walkthrough tonight; live Gateway clip before Aug 31).
6. Work the rest of the checklist in [`docs/SUBMISSION_CHECKLIST.md`](docs/SUBMISSION_CHECKLIST.md).

## What the agent does

Tight ±1.5% SOL/USDC liquidity on Orca Whirlpools via Hummingbot Gateway. When price leaves the band, close and reopen a new tight band (capital-efficiency "leverage" without borrowing). Directional skew, a flush-exhaustion filter, a gas rate-limit, and a 15% drawdown kill-switch sit in front of the official `LPExecutor`.

```
zipline / pandas backtest  -->  YAML params  -->  V2 controller  -->  LPExecutor  -->  Gateway / Orca
         (offline)              (bridge)         (policy)         (deterministic)
```

The LLM never places a trade. Condor is optional later for narration only.

## Repo map

| Path | Role |
|------|------|
| [`submission/`](submission/) | Paste-ready Botcamp fields, `strategy.md`, demo shot list |
| [`docs/DAY_PLAN.md`](docs/DAY_PLAN.md) | Aug 24–31 build calendar |
| [`docs/INSTALL_PLAN.md`](docs/INSTALL_PLAN.md) | Condor + Gateway Docker journey; optional zipline 3.11 |
| [`docs/LEGAL_VENUE_GATE.md`](docs/LEGAL_VENUE_GATE.md) | Why Orca (US ToS) and what is banned |
| [`docs/SHERLOCK_BRIEF.md`](docs/SHERLOCK_BRIEF.md) | Investigation that produced this path |
| [`src/orca_tight_range/logic.py`](src/orca_tight_range/logic.py) | Testable policy (no Hummingbot import) |
| [`controllers/`](controllers/) | V2 controller drop-in |
| [`configs/orca_tight_range.yml`](configs/orca_tight_range.yml) | Race parameters |

## Local smoke test (no Docker)

```bash
cd ~/proj/hummingbot-hackathon
python3 -m pip install -r requirements.txt
python3 -m pytest tests/ -q
python3 research/orca_backtest_zipline.py
python3 research/zipline_to_gateway_bridge.py
```

## Official sources

- Rules: https://www.botcamp.xyz/hackathons/agent-builders-cup-1/resources
- Orca connector: https://hummingbot.org/exchanges/gateway/orca/
- LP executor: https://hummingbot.org/strategies/v2-strategies/executors/
- Example agent: https://www.botcamp.xyz/hackathons/agent-builders-cup-1/resources (`solana-dex-lp-expert`)
