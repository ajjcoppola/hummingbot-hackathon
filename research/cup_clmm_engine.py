"""CLMM mark-to-market + fee napkin for Cup offline search.

Concentration multiplies fees and in-range arbitrage loss together.
A row that only looks good at 200x share is rejected.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]

# Snapshot used in the 2026-09-28 canvas / plan napkin.
POOL_ADDRESS = "Czfq3xZZDmsdGdUyrNLtRhGc47cXcZtLG4crryfu44zE"
POOL_RESERVE_USD = 30_991_339.3884
POOL_FEE = 0.0004  # 0.04%
POOL_VOL_24H_USD = 227_343_377.362512
GAS_PER_RECENTER_USD = 0.02
START_CAPITAL = 800.0
REF_BAND_PCT = 20.0  # reference width for "1x = deposit / reserve"
MAX_ALLOWED_CONC = 20.0  # promotion uses 1x; 20x is diagnostic only
REJECT_CONC = 200.0


@dataclass(frozen=True)
class Candle:
    ts: float
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Napkin:
    turnover: float
    fee_intensity_full_liquidity: float
    deposit_share_of_reserve: float
    fee_usd_per_day_at_1x: float
    fee_usd_per_day_at_20x: float
    note: str


def napkin(
    *,
    reserve: float = POOL_RESERVE_USD,
    vol_24h: float = POOL_VOL_24H_USD,
    fee: float = POOL_FEE,
    capital: float = START_CAPITAL,
) -> Napkin:
    turnover = vol_24h / reserve if reserve > 0 else 0.0
    intensity = turnover * fee
    share = capital / reserve if reserve > 0 else 0.0
    # Fee if you owned `share` of the whole pool with no concentration:
    fee_1x = vol_24h * fee * share
    return Napkin(
        turnover=turnover,
        fee_intensity_full_liquidity=intensity,
        deposit_share_of_reserve=share,
        fee_usd_per_day_at_1x=fee_1x,
        fee_usd_per_day_at_20x=fee_1x * 20.0,
        note=(
            "Concentration k multiplies fee and in-range LVR together. "
            "Promotion requires the 1x book; 200x is rejected."
        ),
    )


def rejects_200x_only(win_at_1x: bool, win_at_20x: bool, win_at_200x: bool) -> bool:
    """True when the only winning concentration is the forbidden 200x slogan."""
    return (not win_at_1x) and (not win_at_20x) and win_at_200x


def load_hourly_candles(path: Path | None = None) -> list[Candle]:
    p = path or (ROOT / "data" / "solusdc_ohlcv_hourly.json")
    raw = json.loads(p.read_text())
    rows = raw["data"]["attributes"]["ohlcv_list"]
    # Gecko returns newest first.
    bars = list(reversed(rows))
    out: list[Candle] = []
    for ts, o, h, l, c, vol in bars:
        out.append(
            Candle(
                ts=float(ts),
                open=float(o),
                high=float(h),
                low=float(l),
                close=float(c),
                volume=float(vol),
            )
        )
    return out


def band_bounds(price: float, full_width_pct: float) -> tuple[float, float]:
    """full_width_pct is the live YAML meaning (1.0 => about ±0.5%)."""
    half = full_width_pct / 200.0
    return price * (1.0 - half), price * (1.0 + half)


def liquidity_from_capital(capital: float, pa: float, pb: float, p: float) -> float:
    sp, spa, spb = math.sqrt(p), math.sqrt(pa), math.sqrt(pb)
    denom = 2.0 * sp - spa - p / spb
    if denom <= 0:
        return 0.0
    return capital / denom


def position_value(L: float, pa: float, pb: float, p: float) -> float:
    spa, spb, sp = math.sqrt(pa), math.sqrt(pb), math.sqrt(max(p, 1e-12))
    if p <= pa:
        return L * (1.0 / spa - 1.0 / spb) * p
    if p >= pb:
        return L * (spb - spa)
    return L * (1.0 / sp - 1.0 / spb) * p + L * (sp - spa)


def initial_mix(L: float, pa: float, pb: float, p: float) -> tuple[float, float]:
    spa, spb, sp = math.sqrt(pa), math.sqrt(pb), math.sqrt(p)
    sol = L * (1.0 / sp - 1.0 / spb)
    usdc = L * (sp - spa)
    return sol, usdc


def concentration_share(
    equity: float,
    *,
    reserve: float = POOL_RESERVE_USD,
    conc: float = 1.0,
) -> float:
    if reserve <= 0 or equity <= 0:
        return 0.0
    return min(1.0, (equity / reserve) * conc)


def fee_on_volume(volume: float, equity: float, *, conc: float, fee: float = POOL_FEE) -> float:
    return volume * fee * concentration_share(equity, conc=conc)


def intra_hour_path(o: float, h: float, l: float, c: float) -> list[float]:
    """Walk open → one extreme → the other → close (order by candle direction)."""
    anchors = [o, l, h, c] if c >= o else [o, h, l, c]
    prices = [anchors[0]]
    for a, b in zip(anchors, anchors[1:]):
        steps = max(1, int(abs(b - a) / (max(a, 1.0) * 0.001)))
        for i in range(1, steps + 1):
            prices.append(a + (b - a) * i / steps)
    return prices


def close_only_path(c: float) -> list[float]:
    return [c]


def slice_train_holdout(
    candles: Sequence[Candle],
    *,
    train_end_ts: float,
) -> tuple[list[Candle], list[Candle]]:
    train = [c for c in candles if c.ts < train_end_ts]
    hold = [c for c in candles if c.ts >= train_end_ts]
    return train, hold


def median(xs: Iterable[float]) -> float:
    arr = sorted(xs)
    if not arr:
        return 0.0
    mid = len(arr) // 2
    if len(arr) % 2:
        return arr[mid]
    return 0.5 * (arr[mid - 1] + arr[mid])


def window_deltas(equity: Sequence[float], window: int = 48) -> list[float]:
    out = []
    for i in range(window, len(equity)):
        out.append(equity[i] - equity[i - window])
    return out
