"""Hourly read-only Orca SOL-USDC pool snapshots for ML training.

Never touches Gateway, Hummingbot, or LP. Appends one JSONL row per hour
to data/pool_snapshots.jsonl with every tier that matches tokensBothOf=SOL,USDC.

Usage:
  python3 research/pool_snapshot_collector.py --once
  python3 research/pool_snapshot_collector.py --interval 3600
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orca_tight_range.pool_rank import (  # noqa: E402
    filter_and_rank,
    score_table,
    snapshot_from_orca_row,
)

ORCA_POOLS = "https://api.orca.so/v2/solana/pools"
MINTS = {
    "SOL": "So11111111111111111111111111111111111111112",
    "USDC": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
}
OUT_PATH = ROOT / "data" / "pool_snapshots.jsonl"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def fetch_sol_usdc(*, size: int = 50) -> list[dict[str, Any]]:
    params = {
        "size": str(size),
        "sortBy": "volume24h",
        "sortDirection": "desc",
        "stats": "24h,7d",
        # tokensBothOf = AND (true SOL-USDC). Do NOT use tokens=SOL,USDC (OR).
        "tokensBothOf": f"{MINTS['SOL']},{MINTS['USDC']}",
    }
    url = f"{ORCA_POOLS}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "hummingbot-hackathon-snapshots/1.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        payload = json.loads(resp.read().decode())
    data = payload.get("data")
    if isinstance(data, dict):
        return list(data.get("pools") or data.get("data") or [])
    if isinstance(data, list):
        return data
    return list(payload.get("pools") or [])


def collect_once(out_path: Path = OUT_PATH) -> dict[str, Any]:
    now_ts = time.time()
    try:
        rows = fetch_sol_usdc()
        pools = [snapshot_from_orca_row(r, source_ts=now_ts) for r in rows]
        ranked = filter_and_rank(pools, now_ts=now_ts)
        record = {
            "ts": utc_now(),
            "ts_unix": now_ts,
            "n_raw": len(rows),
            "n_ranked": len(ranked),
            "top": score_table(ranked, limit=15),
            "pools": [
                {
                    "address": p.address,
                    "fee_pct": p.fee_pct,
                    "tvl": p.tvl_usd,
                    "vol24": p.volume_24h,
                    "vol7d": p.volume_7d,
                    "int24": p.intensity_24h,
                    "int7d": p.intensity_7d,
                    "score": p.score,
                    "has_warning": p.has_warning,
                    "adaptive_fee": p.adaptive_fee,
                    "created_at": p.created_at,
                    "price": p.price,
                }
                for p in pools
            ],
            "error": None,
        }
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as e:
        record = {
            "ts": utc_now(),
            "ts_unix": now_ts,
            "n_raw": 0,
            "n_ranked": 0,
            "top": [],
            "pools": [],
            "error": str(e)[:400],
        }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
    return record


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--once", action="store_true")
    p.add_argument("--interval", type=int, default=3600)
    p.add_argument("--out", type=Path, default=OUT_PATH)
    args = p.parse_args()
    while True:
        rec = collect_once(args.out)
        top0 = (rec.get("top") or [{}])[0] if rec.get("top") else {}
        print(
            json.dumps(
                {
                    "ts": rec["ts"],
                    "n_ranked": rec["n_ranked"],
                    "error": rec.get("error"),
                    "top_addr": (top0.get("address") or "")[:12],
                    "top_score": top0.get("score"),
                }
            ),
            flush=True,
        )
        if args.once:
            break
        time.sleep(max(60, args.interval))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
