#!/usr/bin/env python3
"""Build a one-page tearsheet + simple chart from a reporter run directory.

Reads data/devnet_runs/<run_id>/snapshots.jsonl (+ events.jsonl, meta.json)
and writes tearsheet.md + equity.png (if matplotlib available).

Usage:
  python3 research/make_tearsheet.py --run-id T004_1h_20260922
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def parse_ts(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run-id", required=True)
    args = ap.parse_args()
    run_dir = ROOT / "data" / "devnet_runs" / args.run_id
    if not run_dir.exists():
        raise SystemExit(f"missing {run_dir}")

    meta = {}
    meta_path = run_dir / "meta.json"
    if meta_path.exists():
        meta = json.loads(meta_path.read_text())
    snaps = load_jsonl(run_dir / "snapshots.jsonl")
    events = load_jsonl(run_dir / "events.jsonl")

    ts0 = parse_ts(snaps[0].get("ts")) if snaps else None
    ts1 = parse_ts(snaps[-1].get("ts")) if snaps else None
    hours = ((ts1 - ts0).total_seconds() / 3600.0) if ts0 and ts1 else 0.0
    mtm0 = float(snaps[0].get("total_mtm_quote") or 0) if snaps else 0.0
    mtm1 = float(snaps[-1].get("total_mtm_quote") or 0) if snaps else 0.0
    n_pos = snaps[-1].get("n_positions") if snaps else 0
    in_range = snaps[-1].get("in_range") if snaps else None
    bot_up = sum(1 for s in snaps if s.get("bot_running"))
    uptime_pct = (100.0 * bot_up / len(snaps)) if snaps else 0.0
    txs = [e for e in events if e.get("tx") or e.get("signature") or e.get("type") == "tx"]
    n_tx = len(txs)

    lines = [
        f"# Tearsheet — {args.run_id}",
        "",
        f"- Generated: {datetime.now(timezone.utc).isoformat()}",
        f"- Wallet: `{meta.get('wallet', '')}`",
        f"- Pool: `{meta.get('pool', '')}`",
        f"- Width / trigger: {meta.get('width')} / {meta.get('threshold')}",
        f"- Config quote: {meta.get('total_amount_quote')}",
        f"- Window: {hours:.2f} h ({len(snaps)} snapshots)",
        f"- Start MTM quote: {mtm0:.4f}",
        f"- End MTM quote: {mtm1:.4f}",
        f"- Δ MTM: {mtm1 - mtm0:.4f}",
        f"- Latest positions: {n_pos} (in_range={in_range})",
        f"- Bot uptime (snapshot %): {uptime_pct:.1f}%",
        f"- Event/tx rows: {n_tx}",
        "",
        "## Notes",
        "",
        "- MTM is reporter portfolio mark; not audited P&L.",
        "- Do not claim live edge without a matching `docs/TRIALS_LEDGER.md` row.",
        "",
    ]
    (run_dir / "tearsheet.md").write_text("\n".join(lines), encoding="utf-8")

    # Optional chart
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt

        xs = [parse_ts(s.get("ts")) for s in snaps]
        ys = [float(s.get("total_mtm_quote") or 0) for s in snaps]
        if any(xs) and ys:
            fig, ax = plt.subplots(figsize=(8, 3.5))
            ax.plot(xs, ys, color="#0B6E4F", linewidth=1.5)
            ax.set_title(f"MTM quote — {args.run_id}")
            ax.set_ylabel("quote")
            ax.grid(True, alpha=0.3)
            fig.autofmt_xdate()
            fig.tight_layout()
            fig.savefig(run_dir / "equity.png", dpi=140)
            plt.close(fig)
            lines.append(f"![equity](equity.png)")
            (run_dir / "tearsheet.md").write_text("\n".join(lines), encoding="utf-8")
            print(f"wrote {run_dir / 'equity.png'}")
    except Exception as e:
        print(f"chart_skipped: {e}")

    print(f"wrote {run_dir / 'tearsheet.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
