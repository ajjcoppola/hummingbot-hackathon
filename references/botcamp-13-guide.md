# Hummingbot Botcamp 13: Complete Guide for the Experienced Developer

## Executive Summary

Botcamp Cohort 13 runs April 21 – May 12, 2026, focusing on professional market making and AI-powered agentic trading strategies using Hummingbot's new Condor framework. For US citizens, a viable and growing set of both KYC-compliant CEXs and self-custodial DEXs are accessible through Hummingbot's 50+ exchange connectors. Given your background developing the Coinbase connector and your existing zipline-reloaded/IB stack, the most powerful architectural path is treating the Hummingbot API as a crypto execution middleware that receives signals from your zipline pipeline—an integration that is technically feasible via the new async Python client.[^1][^2][^3][^4][^5]

***

## 1. Hummingbot Condor: Supported Markets

Condor is an open-source harness that connects LLM-powered decision-making to deterministic trade execution via the Hummingbot API, enabling traders to deploy AI agents across 50+ exchanges and blockchains. The key insight of Condor's architecture is a strict separation between the **probabilistic layer** (LLM reasoning) and the **deterministic layer** (Hummingbot execution), so the same instruction always produces the same trade result regardless of LLM variability.[^6][^7][^1]

### CEX Markets (CLOB)

Condor reaches all Hummingbot CLOB connectors. Foundation partners receive priority maintenance:[^8]

| Exchange | Foundation Partner | Spot | Perp | Notes |
|---|---|---|---|---|
| Binance | ✓ | ✓ | ✓ | Highest tier support |
| OKX | ✓ | ✓ | ✓ | Major partner |
| KuCoin | ✓ | ✓ | ✓ | |
| Gate.io | ✓ | ✓ | ✓ | |
| Bitmart | ✓ | ✓ | ✓ | |
| HTX | ✓ | ✓ | – | |
| Coinbase | – | ✓ | – | `coinbase_advanced_trade` v1.0[^9] |
| Kraken | – | ✓ | – | |
| Bitstamp | – | ✓ | – | |
| Bybit | – | ✓ | ✓ | |
| Bitget | ✓ | ✓ | ✓ | |
| Backpack | – | ✓ | ✓ | |

### CLOB DEX Markets

On-chain, non-custodial CLOB exchanges supported include:[^8]

- **Hyperliquid** (perpetuals + HIP-3 spot DEX) — officially restricts US users per ToS[^10]
- **dYdX v4** (perpetuals, Cosmos-based, fully decentralized)[^11]
- **XRPL** (Foundation partner, spot)[^12]
- **Vertex** (spot perpetuals)
- **Dexalot** (spot + perp)
- **Derive** (spot + perp, Foundation partner)

### Gateway DEX (AMM/CLMM)

Hummingbot Gateway provides standardized DEX connectors for AMM and concentrated liquidity protocols:[^13]

| Protocol | Chain | Router | AMM | CLMM |
|---|---|---|---|---|
| Uniswap | Ethereum | ✅ | ✅ | ✅ (V3) |
| PancakeSwap | ETH/BNB | ✅ | ✅ | ✅ |
| Jupiter | Solana | ✅ | – | – |
| Raydium | Solana | – | ✅ | ✅ |
| Meteora | Solana | – | – | ✅ (DLMM) |
| Orca | Solana | – | – | ✅ |

Legacy connectors (need v2.8.0 upgrade, available via bounty): Balancer, Curve, SushiSwap, QuickSwap, TraderJoe.[^13]

***

## 2. US Legal Crypto Trading Options

The US regulatory landscape shifted significantly in early 2026. On March 17, 2026, the SEC and CFTC issued a joint interpretation establishing a taxonomy classifying most digital assets as non-securities. On April 13, 2026, the SEC further clarified that self-custodial wallet interfaces do not require broker-dealer registration—a landmark carve-out for DeFi front-ends and non-custodial platforms.[^14][^15][^16]

### KYC CEX Options for US Traders

The following Hummingbot-connected CEXs are accessible to US citizens with mandatory KYC:

- **Coinbase** — Primary US-regulated CEX; 200+ coins; fiat FDIC-insured up to $250,000; Hummingbot `coinbase_advanced_trade` connector (spot only, v1.0)[^17][^9]
- **Kraken** — 350+ coins, 0%–0.4% fees; Hummingbot spot connector available[^18][^17]
- **Gemini** — NYDFS-regulated, security-focused; 160+ coins; institutional-grade custody; Hummingbot connector available[^19][^20]
- **Bitstamp** — Long-standing regulated CEX; Hummingbot spot connector available[^17][^8]
- **Binance US** — Available in most US states (some state-level restrictions); 158 coins[^17]

### Self-Custody DEX Options (No KYC Required)

US traders can legally trade on self-custodial DEXs using their own wallets. Trades are still taxable events that must be reported to the IRS, but no identity verification is required at the protocol level:[^21][^22]

- **Uniswap (Ethereum)** — Largest DEX by liquidity; V2, V3, and Universal Router; Hummingbot Gateway connector active[^23][^13]
- **Jupiter (Solana)** — Leading Solana aggregator; routes through all Solana DEXs; Hummingbot Gateway connector active[^13]
- **Raydium (Solana)** — Standard AMM + concentrated pools; Hummingbot Gateway connector active[^13]
- **Meteora (Solana)** — DLMM (Dynamic Liquidity Market Maker); well-suited for volatile pairs; Hummingbot CLMM connector[^7][^13]
- **Orca (Solana)** — CLMM pools on Solana; Hummingbot CLMM connector active[^13]
- **PancakeSwap (BNB/ETH)** — V3 Smart Router + AMM; Hummingbot Gateway connector active[^13]
- **dYdX v4** — Fully decentralized perpetual trading (Cosmos-based); no KYC; self-custody[^24][^11]
- **XRPL DEX** — On-chain CLOB, Foundation partner, spot markets[^12][^8]

### Anonymous / Pseudonymous Trading Notes

Self-custody wallets offer the highest degree of pseudonymity. Blockchain transactions are recorded publicly by wallet address, not identity—but wallet addresses can potentially be linked to identities through chain analytics. Best practices for privacy-conscious traders include using hardware wallets (Ledger/Trezor), separating trading wallets from personally identifiable on-chain history, and understanding that all DEX trades remain taxable events regardless of anonymity level.[^25][^22][^21]

**⚠️ Note on Hyperliquid:** While Hyperliquid has no on-chain KYC enforcement, its Terms of Service officially restrict US users. Using it as a US citizen may violate ToS and could carry legal risk depending on future regulatory evolution.[^10]

***

## 3. Botcamp 13 Course Review

### Structure and Format

Botcamp Cohort 13 runs April 21 – May 12, 2026, a 4-week live program with recorded sessions. The program has evolved from an earlier 6-week intensive bootcamp (120+ students across 5 cohorts) into a monthly membership model with live sessions, office hours, and bot trading competitions. The schedule is designed for full-time professionals requiring 5–10 hours per month.[^26][^3][^4]

### Curriculum Themes

Based on the official Botcamp structure and Cohort 13 materials:[^27][^28][^29]

**Week 1 — Foundations**
- Introduction to market making theory
- Running scripts in Hummingbot
- Types of algo trading strategies
- Setting up the V2 framework

**Week 2 — V2 Framework and Agentic Tools**
- V2 architecture: Controllers, Executors
- Introduction to Condor (agentic trading harness)
- Introduction to Hummingbot MCP Server (AI assistant integration)
- Introduction to OpenClaw

**Week 3 — Production Deployment**
- Candles and external data feeds
- Backtesting and optimization
- Deploying strategies in production
- Market making from an operational perspective

**Week 4 — Advanced Strategies and Demo Day**
- Guest lecture from a professional market maker
- Strategy submission and certification
- Demo Day: peer voting, prize categories, Hummingbot certification[^29]

### Strategy Certification

Students who submit a validated strategy at Demo Day receive a professional Hummingbot certification. Many student-built scripts contributed to the official `/scripts` folder in the Hummingbot open-source repo across past cohorts.[^26][^29]

### Sample Projects Using US-Legal Trading

The following projects are feasible for a US trader using the exchanges and DEXs outlined above:

1. **Coinbase/Kraken Pure Market Making Bot** — A classic PMM strategy using the `coinbase_advanced_trade` connector to provide bid/ask liquidity on BTC-USD or ETH-USD. Tune spread parameters using backtesting, then deploy with the V2 framework. Your prior experience with the Coinbase connector gives you a significant advantage here.

2. **Cross-Exchange Arbitrage: Coinbase ↔ Kraken** — Build a XEMM (cross-exchange market making) bot that quotes on Coinbase and hedges on Kraken. Takes advantage of bid-ask spread differences between the two regulated US CEXs.

3. **Solana AMM Liquidity Provision Agent (Meteora/Raydium)** — Use Condor to deploy an autonomous LP agent on Meteora DLMM or Raydium CLMM on Solana. The agent monitors trending pools via GeckoTerminal, deploys concentrated positions within ±5% of spot price, and rebalances automatically. Fully self-custodial, no KYC.[^7]

4. **Uniswap V3 Concentrated Liquidity Manager (Ethereum)** — Build a CLMM management strategy on Uniswap V3 via Gateway. Define narrow tick ranges around current price for high fee capture; auto-rebalance when price exits range. Strategy is LP-focused, not directional.

5. **AI Condor Agent on dYdX Perpetuals** — Create a Condor Agent (`strategy.md`) that uses an LLM (Claude/GPT) to reason about market conditions and adjust perpetual futures positions on dYdX v4. Configure built-in risk guardrails (`max_daily_loss_quote`, `max_drawdown_pct`) and maintain a `journal.md` for persistent learning.[^7]

6. **Jupiter Solana Arbitrage Bot** — Use the Jupiter aggregator (Gateway Router connector) to identify and capture cross-DEX arbitrage opportunities on Solana. Jupiter routes across Raydium, Orca, Meteora and other Solana liquidity sources for optimal execution.

7. **Multi-Exchange Portfolio Rebalancer** — Use the Hummingbot API's portfolio management endpoints to build a rule-based or ML-driven portfolio rebalancer that maintains target allocations across Coinbase (BTC, ETH) and Solana DEX positions (SOL, USDC liquidity), all with self-custodial wallets for the on-chain leg.

***

## 4. Recommendations for Getting into Crypto Market Making

Given your background as an experienced Python/C++ developer with prior Hummingbot Coinbase connector work and zipline-reloaded/IB algo trading experience, the following path is recommended:

### Start with the Coinbase Connector — Upgrade It

The Coinbase connector (`coinbase_advanced_trade`) is currently v1.0 with no V2 Strategies support and no candles feed. Given your prior connector development experience, upgrading it to the V2 standard would be a high-impact contribution that immediately earns you standing in the Hummingbot community and gives you the best local execution environment (compliant, US-native exchange). The upgrade path is documented in the Spot Connector v2.1 Notion template.[^9][^8]

### Learn the Hummingbot API First

The new Hummingbot API is the central hub — it's a FastAPI server with PostgreSQL, EMQX message broker, Docker orchestration, and a Python async client (`pip install hummingbot-api-client`). As an advanced Python developer, start here rather than with the Hummingbot CLI. The API exposes endpoints for account management, portfolio monitoring, order execution, bot orchestration, backtesting, and Gateway DEX management.[^30][^5]

```python
from hummingbot_api_client import HummingbotAPIClient

async with HummingbotAPIClient("http://localhost:8000", "admin", "admin") as client:
    portfolio = await client.portfolio.get_state()
    connectors = await client.connectors.list_connectors()
    order = await client.trading.place_order(
        account_name="master_account",
        connector_name="coinbase_advanced_trade",
        trading_pair="BTC-USD",
        trade_type="BUY",
        amount=0.001,
        order_type="LIMIT",
        price=60000
    )
```

### Build with Condor and MCP

The Condor + MCP workflow is the highest-leverage new capability in Botcamp 13. The MCP Server lets you control your Hummingbot infrastructure using natural language via Claude, ChatGPT, or Gemini — including querying portfolio positions, building CTAs (Controller Trading Algorithms), and analyzing market data conversationally. For an AI developer, this is the most interesting surface area.[^31][^27][^7]

### Use Paper Trading to Validate Before Going Live

All major CEX connectors support paper trading (e.g., `connect coinbase_advanced_trade_paper_trade`). Run strategies in paper mode for at least 2–4 weeks before deploying real capital, tracking metrics like fill rate, spread capture, inventory imbalance, and PnL per unit volume.

### Recommended Entry Path by Risk Level

| Stage | Action | Exchange | Strategy Type |
|---|---|---|---|
| Learn | Botcamp 13 sessions + content library | Paper trade on Coinbase/Kraken | PMM, XEMM |
| Validate | Paper trade on DEX (Solana) | Meteora/Jupiter Gateway | LP / Arbitrage |
| Live (CEX) | Small capital on Coinbase | BTC-USD or ETH-USD PMM | Pure Market Making |
| Live (DEX) | Self-custodial Solana wallet | Raydium/Meteora CLMM | LP Strategy |
| Advanced | Condor agent + LLM reasoning | dYdX perps or Uniswap V3 | Agentic Strategy |

***

## 5. Zipline + Hummingbot Hybrid Architecture

There is no official native integration between zipline-reloaded and Hummingbot, but the pieces to build one are all in place. The core pattern is treating Hummingbot as a crypto execution layer for signals generated by zipline.[^32][^5]

### Architecture Design

The key insight is that zipline's event-driven `handle_data` loop generates trading signals and can call out to external APIs. The Hummingbot API is a locally-running RESTful service that accepts orders synchronously. These two systems can be bridged with a lightweight Python adapter:

```
[zipline-reloaded]                    [Hummingbot API]
  handle_data() →                    FastAPI server
  generate signal →                  ↓
  HummingbotBridge.send_signal() →   /trading/orders
                                     ↓
                             [Coinbase / Kraken / DEX]
                              (execution + fill)
```

The `HummingbotBridge` is a Python class using `hummingbot-api-client` that converts zipline `order()` calls into async Hummingbot API calls:[^5]

```python
import asyncio
from hummingbot_api_client import HummingbotAPIClient
from zipline.api import order, symbol, record

_client = HummingbotAPIClient("http://localhost:8000", "admin", "admin")

def handle_data(context, data):
    # Generate signal from zipline factors/pipeline
    factor_score = data.current(symbol('BTC'), 'momentum')
    if factor_score > context.threshold:
        # Route to Hummingbot for crypto execution
        asyncio.run(_submit_crypto_order("coinbase_advanced_trade", "BTC-USD", 0.001, "BUY"))
    else:
        order(symbol('SPY'), 10)  # Still routes to IB for equities

async def _submit_crypto_order(connector, pair, amount, side):
    await _client.init()
    await _client.trading.place_order(
        account_name="master_account",
        connector_name=connector,
        trading_pair=pair,
        trade_type=side,
        amount=amount,
        order_type="MARKET"
    )
```

### Alternative: Signal Bridge via MQTT

A more decoupled architecture (demonstrated by the TradingView → Hummingbot integration) uses an MQTT broker as a signal bus:[^33]

```
zipline signals → MQTT publish → Hummingbot subscribes → executes trades
```

The MQTT pattern is already part of Hummingbot's internal architecture (EMQX broker), so you'd be working within the existing infrastructure rather than against it.[^30]

### Practical Considerations

- **Zipline clock vs. crypto 24/7**: Zipline uses exchange calendars (NYSE); crypto trades 24/7. The live execution integration requires a custom scheduler or running zipline in continuous mode with `handle_data` on minute bars.
- **Data normalization**: Zipline's `Pipeline` and `DataFetcher` can ingest crypto OHLCV data from external providers (Sharadar doesn't cover crypto, but Alpaca, CoinGecko, or Binance market data can be bundled).[^34][^35]
- **IB + Crypto hybrid portfolio**: Zipline manages the IB equity leg; Hummingbot API manages the crypto leg. Portfolio-level risk is managed at the orchestration layer (Python).
- **Condor for the crypto leg**: Rather than direct API calls from zipline, the crypto leg could be handed to a Condor Agent with a risk-bounded `strategy.md` — the Condor agent receives the signal from zipline and applies its own market microstructure logic on top.[^7]

### Feature Comparison

| Capability | Zipline-Reloaded | Hummingbot | Combined Hybrid |
|---|---|---|---|
| Equities backtesting | ✅ (Sharadar data) | ❌ | ✅ |
| Crypto backtesting | ❌ | ✅ (V2 framework) | ✅ |
| IB live execution | ✅ | ❌ | ✅ |
| CEX execution | ❌ | ✅ (50+ exchanges) | ✅ |
| DEX/AMM execution | ❌ | ✅ (Gateway) | ✅ |
| Factor/pipeline model | ✅ (Alphalens) | ❌ | ✅ |
| LLM agentic strategy | ❌ | ✅ (Condor) | ✅ |
| Market making | ❌ | ✅ | ✅ |

***

## Regulatory & Compliance Notes (US Traders, April 2026)

- **SEC/CFTC joint guidance (March 17, 2026)**: Most digital assets classified as non-securities (commodities); provides first clear federal taxonomy[^36][^16]
- **SEC self-custody wallet guidance (April 13, 2026)**: Software providing access to self-hosted wallets does not require broker-dealer registration if it acts only as an interface and does not take custody, solicit investors, or provide investment advice — valid for 5 years[^15][^14]
- **All DEX trades are taxable**: IRS requires capital gains/losses reporting for crypto-to-crypto trades even on DEXs[^21]
- **Market making regulation**: US crypto market makers trading their own capital (proprietary) are not automatically subject to FINRA rules, but depending on scale and structure, SEC/CFTC jurisdiction may apply[^37]
- **State-level**: New York BitLicense still required for NY-facing activity; California's Digital Finance Assets Law operative July 1, 2026[^38]
- **Individual traders**: Operating personal algo trading bots with your own capital for personal gain generally does not require licensing, but providing trading services to others crosses into registered investment advisor (RIA) territory requiring Series 65 or similar[^37]

---

## References

1. [Condor - Hummingbot](https://hummingbot.org/condor/) - Market access: Connectors to spot, perp, and AMM exchanges, along with Solana and EVM networks; Trad...

2. [Exchanges](https://hummingbot.org/exchanges/) - Hummingbot documentation and website

3. [Botcamp Cohort 13 Preview and Welcome Session · Zoom - Luma](https://luma.com/yrw1a7tj) - In this live welcome session, we'll walk through the cohort structure and logistics, preview the cur...

4. [Botcamp Cohort 13 - Enroll Now](https://www.botcamp.xyz/cohorts/cohort13) - Build and deploy AI-powered trading agents in the newly revamped Cohort 13 curriculum. Apr 21 - May ...

5. [Hummingbot API Client - GitHub](https://github.com/hummingbot/hummingbot-api-client) - An async Python client for the Hummingbot API with modular router support. Installation. pip install...

6. [Introducing Condor: The Open Source Harness for Trading Agents](https://hummingbot.org/blog/introducing-condor-the-open-source-harness-for-trading-agents/) - The Hummingbot API provides deterministic infrastructure: Data collection: Order books, candles, bal...

7. [Introducing Condor Agents: The Open Source Standard for Trading ...](https://hummingbot.org/blog/introducing-condor-agents-the-open-source-standard-for-trading-agents/) - It orchestrates the agentic loop, manages agent state, and connects to execution infrastructure. The...

8. [CLOB Connectors - Hummingbot](https://hummingbot.org/connectors/clob/) - Hummingbot documentation and website

9. [Coinbase - Hummingbot](https://hummingbot.org/exchanges/coinbase/) - Hummingbot documentation and website

10. [What is Hyperliquid? The Complete 2026 Guide - BitMEX](https://www.bitmex.com/blog/what-is-hyperliquid) - Hyperliquid is a self-custodial DEX processing $1-3 billion daily. Here's what traders need to know ...

11. [Best Crypto Exchanges: No KYC Platforms for Anonymous Trading ...](https://blog.tokenmetrics.com/p/best-crypto-exchanges-no-kyc-platforms-for-anonymous-trading-in-2026) - In 2026, it stands out as one of the most powerful tools for users who prefer no-KYC trading. Token ...

12. [Announcements - Hummingbot](https://hummingbot.org/blog/category/announcements/) - This new XRPL connector cements Hummingbot as the open source exchange API connector standard across...

13. [Gateway DEX Connectors - Hummingbot](https://hummingbot.org/gateway/connectors/) - Gateway provides standardized connectors for interacting with decentralized exchanges (DEXs) across ...

14. [SEC Exempts Self-Custodial Crypto Wallets From Broker Registration](https://www.mexc.com/news/1025962) - SEC staff guidance clarifies that non-custodial wallet interfaces won't need broker-dealer registrat...

15. [SEC Lets Self‑Hosted Crypto Wallets Stay Outside Broker Regime ...](https://www.tradingview.com/news/financemagnates:68aa3419f094b:0-sec-lets-self-hosted-crypto-wallets-stay-outside-broker-regime-for-now/) - According to the SEC, the guidance aims to help developers operate without breaching securities laws...

16. [SEC Issues Crypto Guidance as Congress Considers ...](https://www.everycrsreport.com/reports/LSB11415.html) - On March 17, 2026, the Securities and Exchange Commission (SEC) issued guidance addressing the appli...

17. [Best Crypto Exchanges USA March 2026: 10 Expert Picks | Koinly](https://koinly.io/blog/best-crypto-exchange-usa/) - Discover the best crypto exchanges in the USA in 2026! Whether you want security, low fees, trading ...

18. [6 Best Crypto Exchanges of April 2026 | Money](https://money.com/best-crypto-exchanges/) - The best crypto exchange overall for April 2026 is Kraken due to its low fees, powerful data tools, ...

19. [Top 10 Crypto Exchanges in USA in 2026 | Secure and Affordable ...](https://blog.tokenmetrics.com/p/top-10-crypto-exchanges-in-usa-in-2026-secure-and-affordable-trading) - Discover the top 10 crypto exchanges for secure and affordable trading. Find the best platform to me...

20. [Best Crypto Exchanges In USA For April 2026 - Coin Bureau](https://coinbureau.com/analysis/best-crypto-exchanges-usa) - Discover the best crypto exchanges in the USA with The Coin Bureau's expert guide. Compare features,...

21. [6 Best Crypto Decentralized Exchanges of 2026 in the USA](https://coin.space/6-best-crypto-decentralized-exchanges-of-2026-in-the-usa/) - The regulatory landscape for decentralized finance (DeFi) in the United States has shifted dramatica...

22. [Best No-KYC Crypto Exchanges in 2026 - Business Insider](https://www.businessinsider.com/personal-finance/best-no-kyc-crypto-exchanges) - Instead, customers use self-custody wallets that they connect to the DEX, and the DEX serves as a pl...

23. [Uniswap - Hummingbot](https://hummingbot.org/exchanges/gateway/uniswap/) - Configure Uniswap settings in /conf/connectors/uniswap.yml . Below are the Uniswap configuration par...

24. [dYdX: DeFi's Pro Trading Platform](https://www.dydx.xyz) - dYdX offers a decentralized trading platform designed for perpetual contracts, combining deep liquid...

25. [DEX vs CEX vs Instant Exchange: Privacy in 2026 - Godex](https://godex.io/blog/dex-vs-cex-vs-instant-exchange-privacy) - Which crypto exchange is actually private? Compare DEX vs CEX vs instant exchange on KYC, data expos...

26. [Botcamp FAQ - Hummingbothummingbot.org › botcamp › faq](https://hummingbot.org/botcamp/faq/) - Hummingbot documentation and website

27. [Hummingbot Botcamp](https://www.botcamp.xyz) - Education for crypto market makers and algorithmic traders, taught using the Hummingbot open source ...

28. [Botcamp Cohort 13 Info Session - Part 1 - Cohort Schedule](https://www.youtube.com/watch?v=xDr5IrgDJS4) - Learn everything you need to know about Botcamp Cohort 13 - our comprehensive program for learning p...

29. [Events | Hummingbot Botcamp](https://courses.botcamp.xyz/events) - What is a BOTCAMP cohort? A 5-week intensive bootcamp that teaches students to design, code, and dep...

30. [Hummingbot API](https://hummingbot.org/hummingbot-api/) - Hummingbot documentation and website

31. [Hummingbot MCP](https://hummingbot.org/mcp/) - The Hummingbot MCP Server is an interface to Hummingbot API that enables AI assistants like Claude, ...

32. [Hummingbot API Developer Guide](https://hummingbot.org/hummingbot-api/quickstart/) - Hummingbot documentation and website

33. [TradingView, Hummingbot Webhook Trading Strategy - YouTube](https://www.youtube.com/watch?v=AtNbnrZ5VFk) - The overall goal of this strategy is to create a unified, multi-exchange automated trading system th...

34. [Zipline — Zipline 3.0 docs](https://zipline.ml4trading.io)

35. [How to Ingest Premium Market Data with Zipline Reloaded](https://www.interactivebrokers.com/campus/ibkr-quant-news/how-to-ingest-premium-market-data-with-zipline-reloaded/) - This article explains how to build the two Python scripts you need to use premium data to create a c...

36. [The SEC and CFTC's latest crypto guidance - Fidelity Investments](https://www.fidelity.com/learning-center/trading-investing/sec-cftc-crypto-guidance) - The guidance establishes how a legal standard called the Howey Test—which defines whether a transact...

37. [Guide to Crypto Market Maker Regulations – Buzko Krasnov](https://www.buzko.legal/content-eng/guide-to-crypto-market-maker-regulations) - This guide covers legal regulation of market making, challenges posed by decentralized automated mar...

38. [Blockchain & Cryptocurrency Laws & Regulations 2026 | USA](https://www.globallegalinsights.com/practice-areas/blockchain-cryptocurrency-laws-and-regulations/usa/) - This report from Holland & Knight unpacks cryptocurrency laws and regulations in the USA, covering s...

