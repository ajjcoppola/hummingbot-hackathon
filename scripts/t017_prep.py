#!/usr/bin/env python3
"""T017 prep / start gate for the dynamic farmer smoke.

Does NOT start while T016 is still inside its 48h window
(ends 2026-09-30 18:26Z). After that, prints the deploy checklist and
optionally writes a ledger stub.

Usage:
  python3 scripts/t017_prep.py            # status only
  python3 scripts/t017_prep.py --check    # exit 0 only if T016 window ended
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
T016_END = datetime(2026, 9, 30, 18, 26, tzinfo=timezone.utc)
T017_END = datetime(2026, 10, 1, 16, 0, tzinfo=timezone.utc)


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--check", action="store_true", help="exit 1 if T016 still running")
    args = p.parse_args()
    now = datetime.now(timezone.utc)
    remaining = (T016_END - now).total_seconds()
    print(f"now_utc={now.isoformat()}")
    print(f"t016_end={T016_END.isoformat()}")
    print(f"t017_target_end={T017_END.isoformat()}")
    print(f"configs/orca_dynamic_farmer_100.yml ready")
    print(f"fallback=configs/lp_rebalancer_race_800.yml (paste pool after gate PASS)")
    if remaining > 0:
        print(f"STATUS=WAIT t016_remaining_s={int(remaining)}")
        print("Do NOT start T017. Leave T016 untouched.")
        print(
            "Pass criteria when T017 runs: no flat/orphan, <=1 switch, in range, ledger row."
        )
        if args.check:
            return 1
        return 0
    print("STATUS=T016_ENDED — T017 may start on dynamic farmer $100")
    print("Pass = no flat/orphan, <=1 pool switch, position in range, ledger row.")
    print("Fail -> paste ranker top into lp_rebalancer_race_800.yml as race entry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
