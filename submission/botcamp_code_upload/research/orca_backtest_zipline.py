#!/usr/bin/env python3
"""Offline fee/IL/gas simulator for tight-range Whirlpool parameters.

Preferred path is a pandas CSV of SOL/USDC (or SOL/USDT) 1-minute bars.
A zipline-reloaded wrapper is provided for users who already have a 3.11
bundle, but zipline is optional — this file never imports it at module
level so the repo tests run on Python 3.12+.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orca_tight_range.logic import (  # noqa: E402
    Action,
    Params,
    Position,
    Snapshot,
    decide,
    params_to_dict,
)


@dataclass
class Bar:
    ts: float
    close: Decimal


@dataclass
class BacktestResult:
    n_bars: int
    n_opens: int
    n_rebalances: int
    n_deferred: int
    n_rate_limited: int
    n_stops: int
    time_in_range_pct: float
    fee_usdc: float
    realized_il_usdc: float
    gas_usdc: float
    net_usdc: float
    params: dict


def load_csv(path: Path) -> list[Bar]:
    bars: list[Bar] = []
    with path.open() as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            close = row.get("close") or row.get("Close") or row.get("price")
            ts = row.get("timestamp") or row.get("ts") or row.get("date") or str(i)
            if close is None:
                raise ValueError(f"CSV missing close column: {path}")
            try:
                tsf = float(ts)
            except ValueError:
                tsf = float(i * 60)
            bars.append(Bar(ts=tsf, close=Decimal(str(close))))
    if len(bars) < 10:
        raise ValueError("need at least 10 bars")
    return bars


def momentum_sign(closes: list[Decimal]) -> int:
    if len(closes) < 5:
        return 0
    window = closes[-5:]
    delta = window[-1] - window[0]
    if window[0] <= 0:
        return 0
    if abs(delta) / window[0] < Decimal("0.001"):
        return 0
    return 1 if delta > 0 else -1


def bar_returns(closes: list[Decimal]) -> list[Decimal]:
    out = []
    for i in range(1, len(closes)):
        if closes[i - 1] <= 0:
            continue
        out.append((closes[i] / closes[i - 1]) - 1)
    return out[-12:]


def simulate(
    bars: list[Bar],
    params: Params,
    fee_tier: Decimal = Decimal("0.003"),
    volume_usdc_per_bar: Decimal = Decimal("200"),
    sol_usd: Decimal = Decimal("150"),
) -> BacktestResult:
    """Naive CLMM toy model — not a full Whirlpool replay.

    Fee: if in range, earn fee_tier * volume_usdc_per_bar * (our share proxy).
    Share proxy = range tightness vs a 100% full-range book (width/100).
    IL: on each rebalance, charge 0.5 * |spot change since open| * capital.
    Gas: params.gas_sol_per_rebalance * sol_usd per rebalance.
    """
    capital = params.capital_allocation_usdc
    position: Position | None = None
    rebalance_ts: list[float] = []
    closes: list[Decimal] = []
    in_range_bars = 0
    n_opens = n_reb = n_def = n_rl = n_stop = 0
    fee = Decimal("0")
    il = Decimal("0")
    gas = Decimal("0")
    share = Decimal("1") / max(params.range_width_pct, Decimal("0.25"))

    for bar in bars:
        closes.append(bar.close)
        snap = Snapshot(
            ts=bar.ts,
            spot=bar.close,
            equity_usdc=capital + fee - il - gas,
            momentum_sign=momentum_sign(closes),
            recent_returns=bar_returns(closes),
            rebalance_timestamps=rebalance_ts,
        )
        decision = decide(params, snap, position)
        if position and position.lower <= bar.close <= position.upper:
            in_range_bars += 1
            fee += fee_tier * volume_usdc_per_bar * min(share / Decimal("40"), Decimal("1"))

        if decision.action == Action.STOP:
            n_stop += 1
            break
        if decision.event.value == "RebalanceDeferred":
            n_def += 1
        if decision.event.value == "RateLimited":
            n_rl += 1
        if decision.action in (Action.OPEN, Action.REBALANCE) and decision.lower and decision.upper:
            if position is not None:
                move = abs(bar.close - position.center) / position.center
                il += capital * move * Decimal("0.5")
                gas += params.gas_sol_per_rebalance * sol_usd
                n_reb += 1
                rebalance_ts.append(bar.ts)
            else:
                n_opens += 1
            position = Position(
                lower=decision.lower,
                upper=decision.upper,
                center=decision.center or bar.close,
                opened_at=bar.ts,
                opened_equity=capital,
            )

    n = len(bars)
    net = fee - il - gas
    return BacktestResult(
        n_bars=n,
        n_opens=n_opens,
        n_rebalances=n_reb,
        n_deferred=n_def,
        n_rate_limited=n_rl,
        n_stops=n_stop,
        time_in_range_pct=round(100.0 * in_range_bars / n, 2) if n else 0.0,
        fee_usdc=float(fee),
        realized_il_usdc=float(il),
        gas_usdc=float(gas),
        net_usdc=float(net),
        params=params_to_dict(params),
    )


def write_params_json(result: BacktestResult, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(asdict(result), indent=2) + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Tight-range Orca fee/IL/gas backtest")
    parser.add_argument("--csv", type=Path, help="OHLCV CSV with a close column")
    parser.add_argument("--out", type=Path, default=ROOT / "data" / "last_backtest.json")
    parser.add_argument("--width", type=Decimal, default=Decimal("1.5"))
    parser.add_argument("--trigger", type=Decimal, default=Decimal("0.8"))
    parser.add_argument("--skew", type=Decimal, default=Decimal("0.6"))
    args = parser.parse_args()

    params = Params(
        range_width_pct=args.width,
        rebalance_trigger_pct=args.trigger,
        skew_bias=args.skew,
    )
    if args.csv is None:
        # Synthetic 48h of 1m bars: slow drift + one flush, for a dry run.
        price = Decimal("150")
        bars = []
        for i in range(48 * 60):
            if 600 <= i < 605:
                price *= Decimal("0.97")
            else:
                price *= Decimal("1.00002")
            bars.append(Bar(ts=float(i * 60), close=price))
    else:
        bars = load_csv(args.csv)

    result = simulate(bars, params)
    write_params_json(result, args.out)
    print(json.dumps(asdict(result), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
