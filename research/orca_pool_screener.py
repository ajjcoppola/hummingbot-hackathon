#!/usr/bin/env python3
"""Screen Orca mainnet Whirlpools BEFORE joining.

Fetches https://api.orca.so/v2/solana/pools ranked by volume24h, applies
liquidity/volume gates, prints a ranked table + chart URLs, and writes JSON
under data/pool_screens/. Never invents pool addresses. Never writes YAML.

Usage:
  python3 research/orca_pool_screener.py
  python3 research/orca_pool_screener.py --min-vol-24h 5e6 --min-tvl 1e6 --size 25
  python3 research/orca_pool_screener.py --tokens-both SOL,USDC
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
ORCA_POOLS = "https://api.orca.so/v2/solana/pools"

# Well-known mainnet mints (for token filters only — not pool addresses).
MINTS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
    "USDT": "Es9vMFrzaCERmJfrF4H2FYD4KCoNkY11McCe8BenwNYB",
}

# Prefer these for first-join shortlist (still list all PASS rows).
MAJOR_SYMBOLS = frozenset({"SOL", "USDC", "USDT", "WBTC", "CBBTC", "WHETH", "ETH", "BTC"})


def utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")


def fnum(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def fee_pct(fee_rate: Any) -> float:
    # Orca feeRate is in hundredths of a bip (400 => 0.04%).
    return fnum(fee_rate) / 10000.0


def chart_urls(address: str) -> dict[str, str]:
    return {
        "orca": f"https://www.orca.so/pools/{address}",
        "geckoterminal": f"https://www.geckoterminal.com/solana/pools/{address}",
        "dexscreener": f"https://dexscreener.com/solana/{address}",
        "dune_orca_top": "https://dune.com/orca/orca-top-whirlpools",
    }


def fetch_pools(
    *,
    size: int,
    sort_by: str,
    min_tvl: float | None,
    min_vol: float | None,
    tokens_both: list[str] | None,
) -> list[dict[str, Any]]:
    params: dict[str, str] = {
        "size": str(size),
        "sortBy": sort_by,
        "sortDirection": "desc",
        "stats": "24h,7d",
    }
    if min_tvl is not None:
        params["minTvl"] = str(int(min_tvl))
    if min_vol is not None:
        params["minVolume"] = str(int(min_vol))
    if tokens_both:
        mints = []
        for tok in tokens_both:
            key = tok.strip().upper()
            if key in MINTS:
                mints.append(MINTS[key])
            else:
                mints.append(tok.strip())  # allow raw mint
        params["tokensBothOf"] = ",".join(mints)

    url = f"{ORCA_POOLS}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Accept": "application/json", "User-Agent": "orca-pool-screener/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")[:400]
        raise SystemExit(f"Orca API HTTP {e.code}: {detail}") from e
    except urllib.error.URLError as e:
        raise SystemExit(f"Orca API unreachable: {e}") from e

    rows = payload.get("data")
    if not isinstance(rows, list):
        raise SystemExit(f"Unexpected Orca payload keys={list(payload)[:10]}")
    return rows


def normalize(row: dict[str, Any]) -> dict[str, Any]:
    stats = row.get("stats") or {}
    s24 = stats.get("24h") or {}
    s7 = stats.get("7d") or {}
    token_a = row.get("tokenA") or {}
    token_b = row.get("tokenB") or {}
    address = row.get("address") or ""
    pair = f"{token_a.get('symbol', '?')}-{token_b.get('symbol', '?')}"
    vol24 = fnum(s24.get("volume"))
    tvl = fnum(row.get("tvlUsdc"))
    fees24 = fnum(s24.get("fees"))
    return {
        "address": address,
        "pair": pair,
        "token_a": token_a.get("symbol"),
        "token_b": token_b.get("symbol"),
        "fee_rate": row.get("feeRate"),
        "fee_pct": fee_pct(row.get("feeRate")),
        "tvl_usdc": tvl,
        "volume_24h": vol24,
        "fees_24h": fees24,
        "volume_7d": fnum(s7.get("volume")),
        "fees_7d": fnum(s7.get("fees")),
        "yield_over_tvl": fnum(row.get("yieldOverTvl")),
        "has_warning": bool(row.get("hasWarning")),
        "adaptive_fee": bool(row.get("adaptiveFeeEnabled")),
        "price": row.get("price"),
        "fees_per_tvl_24h": (fees24 / tvl) if tvl > 0 else 0.0,
        "charts": chart_urls(address) if address else {},
    }


def gate_row(
    row: dict[str, Any],
    *,
    min_vol_24h: float,
    min_tvl: float,
    allow_warnings: bool,
) -> tuple[bool, list[str]]:
    reasons: list[str] = []
    if not row.get("address"):
        reasons.append("missing_address")
    if row["volume_24h"] < min_vol_24h:
        reasons.append(f"vol24<{min_vol_24h:g}")
    if row["tvl_usdc"] < min_tvl:
        reasons.append(f"tvl<{min_tvl:g}")
    if row["has_warning"] and not allow_warnings:
        reasons.append("hasWarning")
    return (len(reasons) == 0), reasons


def is_major_pair(row: dict[str, Any]) -> bool:
    a = (row.get("token_a") or "").upper()
    b = (row.get("token_b") or "").upper()
    return a in MAJOR_SYMBOLS and b in MAJOR_SYMBOLS


def print_table(rows: list[dict[str, Any]]) -> None:
    header = f"{'rank':>4}  {'PASS':4}  {'pair':12}  {'fee%':>6}  {'TVL$':>12}  {'vol24$':>12}  {'fees24$':>10}  {'f/TVL%':>7}  address"
    print(header)
    print("-" * len(header))
    for i, r in enumerate(rows, 1):
        print(
            f"{i:>4}  {('YES' if r['pass'] else 'no'):4}  {r['pair'][:12]:12}  "
            f"{r['fee_pct']:>6.3f}  {r['tvl_usdc']:>12,.0f}  {r['volume_24h']:>12,.0f}  "
            f"{r['fees_24h']:>10,.0f}  {100 * r['fees_per_tvl_24h']:>7.3f}  {r['address']}"
        )


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--size", type=int, default=25)
    ap.add_argument("--sort-by", default="volume24h")
    ap.add_argument("--min-vol-24h", type=float, default=5_000_000)
    ap.add_argument("--min-tvl", type=float, default=1_000_000)
    ap.add_argument("--allow-warnings", action="store_true")
    ap.add_argument(
        "--tokens-both",
        default="",
        help="Comma symbols or mints that both must be in the pool (e.g. SOL,USDC). Empty = no token filter.",
    )
    ap.add_argument("--out-dir", type=Path, default=ROOT / "data" / "pool_screens")
    args = ap.parse_args()

    tokens = [t for t in args.tokens_both.split(",") if t.strip()] or None
    raw = fetch_pools(
        size=args.size,
        sort_by=args.sort_by,
        min_tvl=args.min_tvl,
        min_vol=args.min_vol_24h,
        tokens_both=tokens,
    )
    ranked: list[dict[str, Any]] = []
    for row in raw:
        norm = normalize(row)
        ok, reasons = gate_row(
            norm,
            min_vol_24h=args.min_vol_24h,
            min_tvl=args.min_tvl,
            allow_warnings=args.allow_warnings,
        )
        norm["pass"] = ok
        norm["fail_reasons"] = reasons
        ranked.append(norm)

    # Prefer PASS → major stables/SOL pairs → volume class → fees/TVL
    for r in ranked:
        r["major_pair"] = is_major_pair(r)
    ranked.sort(
        key=lambda r: (
            r["pass"],
            r["major_pair"],
            r["volume_24h"],
            r["fees_per_tvl_24h"],
        ),
        reverse=True,
    )

    print_table(ranked)
    passed = [r for r in ranked if r["pass"]]
    print()
    print(f"PASS {len(passed)} / {len(ranked)}  (min_vol_24h={args.min_vol_24h:g}, min_tvl={args.min_tvl:g})")
    if passed:
        top = passed[0]
        print()
        print("Top PASS shortlist:")
        print(f"  {top['pair']}  {top['address']}")
        print(f"  fee={top['fee_pct']:.3f}%  TVL=${top['tvl_usdc']:,.0f}  vol24=${top['volume_24h']:,.0f}")
        for name, url in (top.get("charts") or {}).items():
            print(f"  {name}: {url}")
    else:
        print("No PASS pools — relax filters or widen token set.", file=sys.stderr)

    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{utc_stamp()}.json"
    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "filters": {
            "min_vol_24h": args.min_vol_24h,
            "min_tvl": args.min_tvl,
            "sort_by": args.sort_by,
            "tokens_both": tokens,
            "allow_warnings": args.allow_warnings,
        },
        "n_pass": len(passed),
        "pools": ranked,
    }
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print()
    print(f"wrote {out_path}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
