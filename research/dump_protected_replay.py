#!/usr/bin/env python3
"""Offline replay: naked Cup equity path vs dump-protected sleeve+kill.

Uses the cleaned Cup shadow equity series (constant-TVL / same-path caveat):
LP sleeve is assumed to track the naked book's return until the −3% book kill,
then flattens to USDC. Does not model fee differentials from USDC-heavy offset.

Writes docs/blog/czfq-dump-protected-replay.md and optional JSON under data/.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replay(
    points: list[dict],
    *,
    sleeve_pct: float = 0.40,
    kill_pct: float = 0.03,
) -> dict:
    if not points:
        raise ValueError("empty equity points")
    open_eq = float(points[0]["usd"])
    sleeve = open_eq * sleeve_pct
    lp_open = open_eq * (1.0 - sleeve_pct)
    kill_line = open_eq * (1.0 - kill_pct)

    naked: list[dict] = []
    protected: list[dict] = []
    killed_h: float | None = None
    killed_equity: float | None = None
    flat_after = False
    flat_usd = 0.0

    for p in points:
        h = float(p["h"])
        e = float(p["usd"])
        naked.append({"h": h, "usd": e})

        if flat_after:
            protected.append({"h": h, "usd": flat_usd})
            continue

        # LP sleeve tracks naked return (constant-mix caveat).
        lp = lp_open * (e / open_eq) if open_eq > 0 else 0.0
        book = sleeve + lp
        if book <= kill_line:
            flat_after = True
            flat_usd = book  # realize at kill; thereafter USDC
            killed_h = h
            killed_equity = book
            protected.append({"h": h, "usd": flat_usd})
        else:
            protected.append({"h": h, "usd": book})

    naked_close = naked[-1]["usd"]
    prot_close = protected[-1]["usd"]
    hold_usdc = open_eq  # 100% USDC control

    return {
        "open": open_eq,
        "kill_line": kill_line,
        "sleeve_pct": sleeve_pct,
        "kill_pct": kill_pct,
        "naked_close": naked_close,
        "naked_return_pct": (naked_close / open_eq - 1.0) * 100.0,
        "protected_close": prot_close,
        "protected_return_pct": (prot_close / open_eq - 1.0) * 100.0,
        "hold_usdc_return_pct": 0.0,
        "killed_h": killed_h,
        "killed_equity": killed_equity,
        "naked": naked,
        "protected": protected,
        "caveat": (
            "LP sleeve scaled from naked Cup MTM path; does not credit USDC-heavy "
            "offset fee/IL differences. Constant-TVL / same-path approximation."
        ),
    }


def render_md(result: dict) -> str:
    kh = result["killed_h"]
    kill_line = (
        f"Kill fired at hour **{kh:.2f}** (book ≈ ${result['killed_equity']:.2f})."
        if kh is not None
        else "Kill did **not** fire on this path."
    )
    return f"""# Appendix: naked vs dump-protected on Cup window

Offline replay of the Cup shadow equity hours (`data/cup_race_autotimer/equity_48h.json`)
with dump-protected v1 rules: **40% USDC sleeve**, **60% LP** tracking the naked path
until **−3%** book equity, then flatten to USDC.

{result["caveat"]}

## Summary

| Arm | Close | Return |
|-----|-------|--------|
| Hold USDC | ${result["open"]:.2f} | {result["hold_usdc_return_pct"]:+.2f}% |
| Naked 16% LP (actual Cup) | ${result["naked_close"]:.2f} | {result["naked_return_pct"]:+.2f}% |
| Dump-protected v1 (sleeve+kill) | ${result["protected_close"]:.2f} | {result["protected_return_pct"]:+.2f}% |

- Open book: **${result["open"]:.2f}**; kill line: **${result["kill_line"]:.2f}** (−{result["kill_pct"]*100:.0f}%).
- {kill_line}
- Improvement vs naked: **{result["protected_return_pct"] - result["naked_return_pct"]:+.2f}** percentage points (still vs hold-USDC if kill fires after a loss).

Parent post: [`czfq-dump-protected-postmortem.md`](czfq-dump-protected-postmortem.md).
"""


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--equity-json",
        type=Path,
        default=ROOT / "data" / "cup_race_autotimer" / "equity_48h.json",
    )
    ap.add_argument(
        "--out-md",
        type=Path,
        default=ROOT / "docs" / "blog" / "czfq-dump-protected-replay.md",
    )
    ap.add_argument(
        "--out-json",
        type=Path,
        default=ROOT / "data" / "cup_race_autotimer" / "dump_protected_replay.json",
    )
    args = ap.parse_args()

    raw = json.loads(args.equity_json.read_text(encoding="utf-8"))
    points = raw["points"] if isinstance(raw, dict) else raw
    result = replay(points)
    slim = {k: v for k, v in result.items() if k not in ("naked", "protected")}
    slim["n_points"] = len(result["naked"])
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps({**slim, "naked": result["naked"], "protected": result["protected"]}, indent=2) + "\n")
    args.out_md.parent.mkdir(parents=True, exist_ok=True)
    args.out_md.write_text(render_md(result), encoding="utf-8")
    print(json.dumps(slim, indent=2))
    print(f"wrote {args.out_md}")
    print(f"wrote {args.out_json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
