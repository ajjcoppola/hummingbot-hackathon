#!/usr/bin/env python3
"""One-screen health digest for the Devnet LP stack.

Summarizes:
- current bot status + open positions from the Hummingbot API
- latest reporter run under data/devnet_runs/
- recent watchdog actions under data/devnet_watchdog/

Read-only helper for quick check-ins after being away.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from devnet_run_reporter import ApiClient, DEFAULT_POOL, DEFAULT_WALLET

ROOT = Path(__file__).resolve().parents[1]


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def latest_run_dir() -> Path | None:
    root = ROOT / "data" / "devnet_runs"
    if not root.exists():
        return None
    dirs = [p for p in root.iterdir() if p.is_dir()]
    if not dirs:
        return None
    return max(dirs, key=lambda p: p.stat().st_mtime)


def current_state(client: ApiClient, instance_prefix: str, pool: str, wallet: str) -> dict[str, Any]:
    status = client.request("GET", "/bot-orchestration/status") or {}
    data = status.get("data") or {}
    bots = {name: meta for name, meta in data.items() if name.startswith(instance_prefix)}
    running = [name for name, meta in bots.items() if (meta or {}).get("status") == "running"]

    positions = client.request(
        "POST",
        "/gateway/clmm/positions_owned",
        {
            "connector": "orca",
            "network": "solana-devnet",
            "pool_address": pool,
            "wallet_address": wallet,
        },
        timeout=60.0,
    )
    if not isinstance(positions, list):
        positions = []
    return {"bots": bots, "running": running, "positions": positions}


def summarize_reporter(run_dir: Path | None) -> list[str]:
    if run_dir is None:
        return ["Reporter: no run directories yet"]

    snapshots = read_jsonl(run_dir / "snapshots.jsonl")
    events = read_jsonl(run_dir / "events.jsonl")
    report = run_dir / "report.md"

    lines = [f"Reporter: {run_dir.name}"]
    if not snapshots:
        lines.append("  snapshots: none yet")
    else:
        first = snapshots[0]
        last = snapshots[-1]
        t0 = parse_ts(first.get("ts"))
        t1 = parse_ts(last.get("ts"))
        hours = ((t1 - t0).total_seconds() / 3600.0) if t0 and t1 else 0.0
        lines.append(
            f"  window: {first.get('ts')} -> {last.get('ts')} ({hours:.2f}h, {len(snapshots)} snapshots)"
        )
        lines.append(
            f"  latest: positions={last.get('n_positions')} in_range={last.get('in_range')} "
            f"mtm={float(last.get('total_mtm_quote') or 0):.4f}"
        )

    if events:
        types = Counter((ev.get("type") or ev.get("event_type") or "event") for ev in events)
        top = ", ".join(f"{k}:{v}" for k, v in types.most_common(5))
        lines.append(f"  events: {len(events)} ({top})")
    else:
        lines.append("  events: none yet")

    lines.append(f"  finalized_report: {'yes' if report.exists() else 'no'}")
    return lines


def summarize_watchdog() -> list[str]:
    path = ROOT / "data" / "devnet_watchdog" / "watchdog.jsonl"
    rows = read_jsonl(path)
    if not rows:
        return ["Watchdog: no entries yet"]
    recent = rows[-5:]
    lines = [f"Watchdog: {len(rows)} entries total"]
    for row in recent:
        lines.append(
            f"  {row.get('ts')} action={row.get('action')} positions={row.get('n_positions')} "
            f"running={len(row.get('running_bots') or [])} detail={row.get('detail')}"
        )
    return lines


def summarize_risks(state: dict[str, Any], run_dir: Path | None) -> list[str]:
    risks: list[str] = []
    positions = state["positions"]
    running = state["running"]

    if len(running) == 0:
        risks.append("bot is not running")
    elif len(running) > 1:
        risks.append(f"multiple running bots: {len(running)}")

    if len(positions) == 0:
        risks.append("wallet is flat (no open LP)")
    elif len(positions) > 1:
        risks.append(f"duplicate LP positions detected: {len(positions)}")

    latest = None
    if run_dir:
        snaps = read_jsonl(run_dir / "snapshots.jsonl")
        if snaps:
            latest = snaps[-1]
    if latest and latest.get("bot_running") is False:
        risks.append("latest reporter snapshot saw bot stopped")

    if not risks:
        risks.append("no obvious red flags")
    return risks


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--api", default="http://127.0.0.1:8000")
    p.add_argument("--instance-prefix", default="orca_tight_devnet")
    p.add_argument("--pool", default=DEFAULT_POOL)
    p.add_argument("--wallet", default=DEFAULT_WALLET)
    args = p.parse_args()

    client = ApiClient(args.api)
    state = current_state(client, args.instance_prefix, args.pool, args.wallet)
    run_dir = latest_run_dir()

    now = datetime.now(timezone.utc).isoformat()
    print(f"Devnet Health Digest @ {now}")
    print("")
    print("Current")
    print(f"  running_bots: {len(state['running'])} {state['running']}")
    print(f"  open_positions: {len(state['positions'])}")
    for pos in state["positions"][:3]:
        print(
            f"    {pos.get('position_address')} in_range={pos.get('in_range')} "
            f"base={pos.get('base_token_amount')} quote={pos.get('quote_token_amount')}"
        )

    print("")
    for line in summarize_reporter(run_dir):
        print(line)

    print("")
    for line in summarize_watchdog():
        print(line)

    print("")
    print("Risk Summary")
    for risk in summarize_risks(state, run_dir):
        print(f"  - {risk}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
