#!/usr/bin/env python3
"""Devnet endurance reporter — dual-source snapshots + trade report.

Polls Hummingbot API (portfolio, positions, bot status, CLMM events) and
optionally scrapes Gateway docker logs for tx signatures. On --finalize,
writes report.md + trades.csv under data/devnet_runs/<run_id>/.

Auth via HB_API_USER / HB_API_PASS (default admin/admin). Never commit secrets.
"""

from __future__ import annotations

import argparse
import base64
import csv
import json
import os
import re
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_POOL = "3KBZiL2g8C7tiJ32hTv5v3KM7aK9htpqTw4cTXz1HvPt"
DEFAULT_WALLET = "2ZuShDjgEkdiTtEqbSSCzGUhh5kaFqMjhiuC2VPUNXoB"
DEFAULT_NETWORK = "solana-devnet"
DEFAULT_QUOTE_TOKEN = "devUSDC"
TX_RE = re.compile(r"(?:Sent transaction|Transaction|Orca swap executed:)\s+([1-9A-HJ-NP-Za-km-z]{64,88})")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def api_auth_header() -> str:
    user = os.environ.get("HB_API_USER", "admin")
    password = os.environ.get("HB_API_PASS", "admin")
    token = base64.b64encode(f"{user}:{password}".encode()).decode()
    return f"Basic {token}"


class ApiClient:
    def __init__(self, base: str = "http://127.0.0.1:8000"):
        self.base = base.rstrip("/")
        self.auth = api_auth_header()

    def request(self, method: str, path: str, body: Optional[dict] = None, timeout: float = 30.0) -> Any:
        data = None if body is None else json.dumps(body).encode()
        req = urllib.request.Request(
            f"{self.base}{path}",
            data=data,
            method=method,
            headers={
                "Authorization": self.auth,
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                raw = resp.read().decode()
                return json.loads(raw) if raw else None
        except urllib.error.HTTPError as e:
            detail = e.read().decode(errors="replace")[:500]
            raise RuntimeError(f"HTTP {e.code} {path}: {detail}") from e
        except urllib.error.URLError as e:
            raise RuntimeError(f"API unreachable {path}: {e}") from e


def append_jsonl(path: Path, row: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(row, default=str) + "\n")


def load_jsonl(path: Path) -> List[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            rows.append(json.loads(line))
    return rows


def scrape_gateway_logs(since_seconds: int = 120) -> List[dict]:
    """Best-effort parse of Gateway docker logs for tx signatures."""
    try:
        out = subprocess.check_output(
            ["docker", "logs", "gateway", f"--since={since_seconds}s"],
            stderr=subprocess.STDOUT,
            text=True,
            timeout=20,
        )
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        return []
    events = []
    for line in out.splitlines():
        m = TX_RE.search(line)
        if not m:
            continue
        kind = "swap" if "swap" in line.lower() else "tx"
        if "open" in line.lower() or "Position created" in line:
            kind = "open"
        if "closed" in line.lower() or "Position closed" in line:
            kind = "close"
        events.append(
            {
                "ts": utc_now(),
                "source": "gateway_logs",
                "type": kind,
                "tx": m.group(1),
                "raw": line[-240:],
            }
        )
    return events


def token_units(portfolio: dict, token: str, network: str = DEFAULT_NETWORK) -> float:
    """Accept either full /portfolio/state or a single account's network map."""
    if not portfolio:
        return 0.0
    # Full response: {account: {network: [rows]}}
    if any(isinstance(v, dict) for v in portfolio.values()):
        for _account, nets in portfolio.items():
            if not isinstance(nets, dict):
                continue
            for row in nets.get(network) or []:
                if row.get("token") == token:
                    return float(row.get("units") or row.get("available_units") or 0)
        return 0.0
    # Single account map: {network: [rows]}
    for row in portfolio.get(network) or []:
        if isinstance(row, dict) and row.get("token") == token:
            return float(row.get("units") or row.get("available_units") or 0)
    return 0.0


def snapshot_once(
    client: ApiClient,
    pool: str,
    wallet: str,
    bot_filter: Optional[str],
    network: str = DEFAULT_NETWORK,
    quote_token: str = DEFAULT_QUOTE_TOKEN,
) -> dict:
    portfolio = client.request("POST", "/portfolio/state", {})
    positions = client.request(
        "POST",
        "/gateway/clmm/positions_owned",
        {
            "connector": "orca",
            "network": network,
            "pool_address": pool,
            "wallet_address": wallet,
        },
    )
    if not isinstance(positions, list):
        positions = []

    bot_status: Dict[str, Any] = {}
    try:
        status = client.request("GET", "/bot-orchestration/status")
        data = (status or {}).get("data") or {}
        if bot_filter:
            bot_status = {k: v for k, v in data.items() if bot_filter in k}
        else:
            bot_status = {k: v for k, v in data.items() if "orca" in k.lower()}
    except RuntimeError as e:
        bot_status = {"error": str(e)}

    pool_info = {}
    try:
        pool_info = client.request(
            "GET",
            f"/gateway/clmm/pool-info?connector=orca&network={network}&pool_address={pool}",
        )
    except RuntimeError:
        pool_info = {}

    price = float((pool_info or {}).get("price") or 0)
    sol = token_units(portfolio.get("master_account", portfolio), "SOL", network=network)
    usdc = token_units(portfolio.get("master_account", portfolio), quote_token, network=network)

    lp_base = sum(float(p.get("base_token_amount") or 0) for p in positions)
    lp_quote = sum(float(p.get("quote_token_amount") or 0) for p in positions)
    fee_base = sum(float(p.get("base_fee_amount") or 0) for p in positions)
    fee_quote = sum(float(p.get("quote_fee_amount") or 0) for p in positions)
    in_range = any(bool(p.get("in_range")) for p in positions) if positions else None

    lp_mtm = lp_base * price + lp_quote
    wallet_mtm = sol * price + usdc
    total_mtm = wallet_mtm + lp_mtm

    running = any((v or {}).get("status") == "running" for v in bot_status.values() if isinstance(v, dict))

    return {
        "ts": utc_now(),
        "sol": sol,
        "devUSDC": usdc,  # historical key; holds quote_token units (devUSDC or USDC)
        "quote_token": quote_token,
        "network": network,
        "pool_price": price,
        "lp_base": lp_base,
        "lp_quote": lp_quote,
        "fee_base": fee_base,
        "fee_quote": fee_quote,
        "in_range": in_range,
        "n_positions": len(positions),
        "positions": [
            {
                "address": p.get("position_address"),
                "lower": p.get("lower_price"),
                "upper": p.get("upper_price"),
                "in_range": p.get("in_range"),
                "base": p.get("base_token_amount"),
                "quote": p.get("quote_token_amount"),
            }
            for p in positions
        ],
        "wallet_mtm_quote": wallet_mtm,
        "lp_mtm_quote": lp_mtm,
        "total_mtm_quote": total_mtm,
        "bot_running": running,
        "bots": {k: (v or {}).get("status") for k, v in bot_status.items()},
    }


def collect_position_events(client: ApiClient, position_addresses: List[str]) -> List[dict]:
    events = []
    for addr in position_addresses:
        try:
            resp = client.request("GET", f"/gateway/clmm/positions/{addr}/events?limit=200")
            for ev in (resp or {}).get("data") or []:
                events.append({"ts": utc_now(), "source": "clmm_events", "position": addr, **ev})
        except RuntimeError as e:
            events.append({"ts": utc_now(), "source": "clmm_events", "position": addr, "error": str(e)})
    return events


def finalize_report(run_dir: Path, meta: dict) -> None:
    snapshots = load_jsonl(run_dir / "snapshots.jsonl")
    events = load_jsonl(run_dir / "events.jsonl")

    trades: List[dict] = []
    seen_tx = set()
    for ev in events:
        tx = ev.get("tx") or ev.get("transaction_hash") or ev.get("signature")
        etype = ev.get("type") or ev.get("event_type") or "event"
        key = f"{etype}:{tx}"
        if tx and key in seen_tx:
            continue
        if tx:
            seen_tx.add(key)
        trades.append(
            {
                "ts": ev.get("ts") or ev.get("timestamp") or "",
                "type": etype,
                "tx": tx or "",
                "base": ev.get("base") or ev.get("base_token_amount") or "",
                "quote": ev.get("quote") or ev.get("quote_token_amount") or "",
                "fee": ev.get("fee") or "",
                "notes": (ev.get("raw") or ev.get("error") or ev.get("position") or "")[:200],
            }
        )

    t0 = snapshots[0] if snapshots else None
    t1 = snapshots[-1] if snapshots else None
    hours = 0.0
    if t0 and t1:
        try:
            a = datetime.fromisoformat(t0["ts"])
            b = datetime.fromisoformat(t1["ts"])
            hours = max(0.0, (b - a).total_seconds() / 3600.0)
        except ValueError:
            hours = 0.0

    in_range_n = sum(1 for s in snapshots if s.get("in_range") is True)
    in_range_pct = (100.0 * in_range_n / len(snapshots)) if snapshots else 0.0
    mtm0 = float((t0 or {}).get("total_mtm_quote") or 0)
    mtm1 = float((t1 or {}).get("total_mtm_quote") or 0)
    fee_quote = float((t1 or {}).get("fee_quote") or 0)
    fee_base = float((t1 or {}).get("fee_base") or 0)
    price1 = float((t1 or {}).get("pool_price") or 0)
    fees_quote = fee_quote + fee_base * price1
    sol0 = float((t0 or {}).get("sol") or 0)
    sol1 = float((t1 or {}).get("sol") or 0)
    gas_sol = sol0 - sol1  # naive; includes LP deposits — annotate honestly

    csv_path = run_dir / "trades.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["ts", "type", "tx", "base", "quote", "fee", "notes"])
        w.writeheader()
        for row in trades:
            w.writerow(row)

    network = meta.get("network") or DEFAULT_NETWORK
    quote_token = meta.get("quote_token") or DEFAULT_QUOTE_TOKEN
    cluster = "" if "mainnet" in network else "?cluster=devnet"
    explorer = "https://explorer.solana.com/tx/{tx}" + cluster
    venue_label = "mainnet" if "mainnet" in network else "Devnet"
    lines = [
        f"# {venue_label} endurance report — `{run_dir.name}`",
        "",
        f"- Generated: `{utc_now()}`",
        f"- Wallet: `{meta.get('wallet')}`",
        f"- Pool: `{meta.get('pool')}`",
        f"- Network: `{network}` / quote `{quote_token}` / orca/clmm",
        f"- Params: width={meta.get('width')} threshold={meta.get('threshold')} total_amount_quote={meta.get('total_amount_quote')}",
        f"- Window hours: **{hours:.3f}** ({len(snapshots)} snapshots)",
        f"- In-range snapshots: **{in_range_pct:.1f}%** ({in_range_n}/{len(snapshots)})",
        "",
        f"## Mark-to-market (quote = pool price × SOL + {quote_token} + LP inventory)",
        "",
        f"| | t0 | t1 | delta |",
        f"|--|--|--|--|",
        f"| total_mtm_quote | {mtm0:.6f} | {mtm1:.6f} | {mtm1 - mtm0:.6f} |",
        f"| SOL | {sol0:.6f} | {sol1:.6f} | {sol1 - sol0:.6f} |",
        f"| {quote_token} | {(t0 or {}).get('devUSDC', 0)} | {(t1 or {}).get('devUSDC', 0)} | — |",
        f"| LP base | {(t0 or {}).get('lp_base', 0)} | {(t1 or {}).get('lp_base', 0)} | — |",
        f"| LP quote | {(t0 or {}).get('lp_quote', 0)} | {(t1 or {}).get('lp_quote', 0)} | — |",
        "",
        f"- Pending LP fees (quote equiv): **{fees_quote:.8f}**",
        f"- Naive SOL delta (includes LP/rent/swaps, not pure gas): **{gas_sol:.6f} SOL**",
        f"- Bot running at end: **{(t1 or {}).get('bot_running')}** — bots `{(t1 or {}).get('bots')}`",
        "",
        "## Trades / events",
        "",
    ]
    if not trades:
        lines.append("_No open/close/swap signatures captured — hold-only or API/log scrape empty._")
        lines.append("")
    else:
        lines.append("| ts | type | tx | notes |")
        lines.append("|----|------|----|-------|")
        for row in trades:
            tx = row["tx"]
            link = f"[`{tx[:12]}…`]({explorer.format(tx=tx)})" if tx else ""
            lines.append(f"| {row['ts']} | {row['type']} | {link} | {row['notes'][:80]} |")
        lines.append("")

    lines.extend(
        [
            "## Honesty notes",
            "",
            f"- Venue: `{network}` — record facts only in docs/TRIALS_LEDGER.md.",
            "- Quiet pool / HOLD may produce zero rebalances; that is a valid result.",
            "- Do not invent Sharpe. Mainnet fills are taxable.",
            "",
            f"Artifacts: `{csv_path.name}`, `snapshots.jsonl`, `events.jsonl`",
            "",
        ]
    )
    (run_dir / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {run_dir / 'report.md'} and {csv_path}")


def run_poll(args: argparse.Namespace) -> int:
    run_dir = ROOT / "data" / "devnet_runs" / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    meta = {
        "wallet": args.wallet,
        "pool": args.pool,
        "network": args.network,
        "quote_token": args.quote_token,
        "width": args.width,
        "threshold": args.threshold,
        "total_amount_quote": args.total_amount_quote,
        "started": utc_now(),
    }
    (run_dir / "meta.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    client = ApiClient(args.api)
    stop = {"flag": False}

    def _stop(_sig, _frame):
        stop["flag"] = True

    signal.signal(signal.SIGINT, _stop)
    signal.signal(signal.SIGTERM, _stop)

    deadline = time.time() + args.duration_s if args.duration_s > 0 else None
    print(f"polling every {args.interval}s → {run_dir} (Ctrl-C or duration to finalize)")

    known_positions: set = set()
    while not stop["flag"]:
        try:
            snap = snapshot_once(
                client,
                args.pool,
                args.wallet,
                args.bot_filter,
                network=args.network,
                quote_token=args.quote_token,
            )
            append_jsonl(run_dir / "snapshots.jsonl", snap)
            for p in snap.get("positions") or []:
                addr = p.get("address")
                if addr and addr not in known_positions:
                    known_positions.add(addr)
                    for ev in collect_position_events(client, [addr]):
                        append_jsonl(run_dir / "events.jsonl", ev)
            for ev in scrape_gateway_logs(since_seconds=max(args.interval + 30, 90)):
                append_jsonl(run_dir / "events.jsonl", ev)
            print(
                f"{snap['ts']} mtm={snap['total_mtm_quote']:.4f} "
                f"pos={snap['n_positions']} in_range={snap['in_range']} "
                f"bot={snap['bot_running']}"
            )
        except Exception as e:
            append_jsonl(run_dir / "events.jsonl", {"ts": utc_now(), "source": "reporter", "type": "error", "error": str(e)})
            print(f"ERROR {e}", file=sys.stderr)

        if deadline and time.time() >= deadline:
            break
        time.sleep(args.interval)

    finalize_report(run_dir, meta)
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run-id", required=True, help="e.g. T004_1h_20260904")
    p.add_argument("--finalize-only", action="store_true", help="Rebuild report from existing JSONL")
    p.add_argument("--duration-s", type=int, default=0, help="Stop after N seconds (0 = until Ctrl-C)")
    p.add_argument("--interval", type=int, default=60, help="Poll interval seconds")
    p.add_argument("--api", default=os.environ.get("HB_API_URL", "http://127.0.0.1:8000"))
    p.add_argument("--pool", default=DEFAULT_POOL)
    p.add_argument("--wallet", default=DEFAULT_WALLET)
    p.add_argument("--network", default=DEFAULT_NETWORK, help="e.g. solana-devnet or solana-mainnet-beta")
    p.add_argument("--quote-token", default=DEFAULT_QUOTE_TOKEN, help="devUSDC (devnet) or USDC (mainnet)")
    p.add_argument("--bot-filter", default="orca_tight")
    p.add_argument("--width", default="1.5")
    p.add_argument("--threshold", default="0.8")
    p.add_argument("--total-amount-quote", default="20")
    args = p.parse_args()

    run_dir = ROOT / "data" / "devnet_runs" / args.run_id
    if args.finalize_only:
        meta_path = run_dir / "meta.json"
        meta = json.loads(meta_path.read_text()) if meta_path.exists() else {
            "wallet": args.wallet,
            "pool": args.pool,
            "network": args.network,
            "quote_token": args.quote_token,
            "width": args.width,
            "threshold": args.threshold,
            "total_amount_quote": args.total_amount_quote,
        }
        finalize_report(run_dir, meta)
        return 0
    return run_poll(args)


if __name__ == "__main__":
    raise SystemExit(main())
