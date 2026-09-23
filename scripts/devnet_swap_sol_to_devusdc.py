#!/usr/bin/env python3
"""Devnet SOL → devUSDC swap via Gateway's real Orca CLMM route.

Hummingbot API's POST /gateway/swap/execute currently maps Orca to
  /trading/clmm/execute-swap
which Gateway 2.16 does not expose (404). This helper calls the working path:
  /connectors/orca/clmm/execute-swap
from inside the hummingbot-api container (mTLS + passphrase already configured).

Usage (from host):
  python3 scripts/devnet_swap_sol_to_devusdc.py --amount 3
  python3 scripts/devnet_swap_sol_to_devusdc.py --amount 0.05 --quote-only
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys


INNER = r'''
import asyncio, json, os, sys
from services.gateway_client import GatewayClient
from utils.gateway_certs import build_client_ssl_context

amount = float(os.environ["SWAP_AMOUNT"])
quote_only = os.environ.get("QUOTE_ONLY") == "1"
pool = os.environ.get("POOL", "3KBZiL2g8C7tiJ32hTv5v3KM7aK9htpqTw4cTXz1HvPt")
wallet = os.environ.get("WALLET", "2ZuShDjgEkdiTtEqbSSCzGUhh5kaFqMjhiuC2VPUNXoB")
slip = float(os.environ.get("SLIPPAGE_PCT", "2"))
pw = os.environ.get("CONFIG_PASSWORD") or os.environ.get("GATEWAY_PASSPHRASE")
url = os.environ.get("GATEWAY_URL", "https://gateway:15888")
client = GatewayClient(url, ssl_context_factory=lambda: build_client_ssl_context(pw))

async def main():
    q = await client._request("GET", "connectors/orca/clmm/quote-swap", params={
        "network": "devnet",
        "poolAddress": pool,
        "baseToken": "SOL",
        "quoteToken": "devUSDC",
        "amount": str(amount),
        "side": "SELL",
        "slippagePct": str(slip),
    })
    print("QUOTE", json.dumps(q))
    if quote_only:
        return
    result = await client._request("POST", "connectors/orca/clmm/execute-swap", json={
        "network": "devnet",
        "walletAddress": wallet,
        "poolAddress": pool,
        "baseToken": "SOL",
        "quoteToken": "devUSDC",
        "amount": amount,
        "side": "SELL",
        "slippagePct": slip,
    })
    print("EXECUTE", json.dumps(result))
    await client.close()

asyncio.run(main())
'''


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--amount", type=float, required=True, help="SOL to sell")
    ap.add_argument("--quote-only", action="store_true")
    ap.add_argument("--slippage-pct", type=float, default=2.0)
    ap.add_argument(
        "--wallet",
        default="2ZuShDjgEkdiTtEqbSSCzGUhh5kaFqMjhiuC2VPUNXoB",
    )
    ap.add_argument(
        "--pool",
        default="3KBZiL2g8C7tiJ32hTv5v3KM7aK9htpqTw4cTXz1HvPt",
    )
    args = ap.parse_args()

    cmd = [
        "docker",
        "exec",
        "-e",
        f"SWAP_AMOUNT={args.amount}",
        "-e",
        f"QUOTE_ONLY={'1' if args.quote_only else '0'}",
        "-e",
        f"SLIPPAGE_PCT={args.slippage_pct}",
        "-e",
        f"WALLET={args.wallet}",
        "-e",
        f"POOL={args.pool}",
        "-i",
        "hummingbot-api",
        "python",
        "-",
    ]
    try:
        proc = subprocess.run(cmd, input=INNER, text=True, check=False)
    except FileNotFoundError:
        print("docker not found / OrbStack not running", file=sys.stderr)
        return 2
    return proc.returncode


if __name__ == "__main__":
    raise SystemExit(main())
