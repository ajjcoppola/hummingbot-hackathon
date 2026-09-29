#!/usr/bin/env python3
"""Offline Cup money search — five rules, holdout, napkin gate.

Does not touch T016 / Gateway / live YAML.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
sys.path.insert(0, str(ROOT / "src"))

from cup_clmm_engine import (  # noqa: E402
    GAS_PER_RECENTER_USD,
    POOL_ADDRESS,
    POOL_FEE,
    POOL_RESERVE_USD,
    START_CAPITAL,
    Candle,
    band_bounds,
    close_only_path,
    fee_on_volume,
    initial_mix,
    intra_hour_path,
    liquidity_from_capital,
    load_hourly_candles,
    median,
    napkin,
    position_value,
    rejects_200x_only,
    window_deltas,
)
from orca_tight_range.logic import (  # noqa: E402
    Action,
    Params,
    Position,
    Snapshot,
    decide,
)
from decimal import Decimal


# Train ends 2026-09-21 00:00Z; holdout is the rest through 28 Sep.
TRAIN_END_TS = datetime(2026, 9, 21, tzinfo=timezone.utc).timestamp()
BASELINE_LP_TARGET = 243.0
BASELINE_HODL_TARGET = 858.0
BASELINE_TOL_LP = 40.0
BASELINE_TOL_HODL = 25.0


@dataclass
class RuleConfig:
    name: str
    full_width_pct: float
    trigger_pct: float = 0.05
    hourly_cap: Optional[int] = None
    skew: float = 0.5
    exhaustion: bool = False
    # sit_wide / do_not_chase / chop_gate knobs
    max_rebals_per_day: int = 2
    vol_gate: float = 0.012  # hourly abs return threshold for chop
    trend_gate: float = 0.03  # 24h abs return => trend (do-not-chase)


@dataclass
class ReplayResult:
    rule: str
    path: str
    conc: float
    full_width_pct: float
    trigger_pct: float
    hourly_cap: Optional[int]
    end_equity: float
    end_hodl: float
    fees: float
    gas: float
    n_rebals: float
    in_range_pct: float
    median_48h_lp: float
    median_48h_hodl: float
    median_48h_edge: float
    bot_vol: float
    trend_gate: float = 0.0
    vol_gate: float = 0.0
    skew: float = 0.5
    exhaustion: bool = False
    daily: list[dict[str, Any]] = field(default_factory=list)
    rejected_200x_only: bool = False
    notes: str = ""


def _dec(x: float) -> Decimal:
    return Decimal(str(x))


class Book:
    """One concentrated position + fee/gas ledger."""

    def __init__(self, capital: float, pa: float, pb: float, p: float):
        self.L = liquidity_from_capital(capital, pa, pb, p)
        self.pa = pa
        self.pb = pb
        self.fees_open = 0.0
        self.fees_tot = 0.0
        self.gas = 0.0
        self.n_rebals = 0
        self.bot_vol = capital
        self.hodl_sol, self.hodl_usdc = initial_mix(self.L, pa, pb, p)
        self.flat_cash = 0.0  # when ChopGate exits to hold mix
        self.in_pool = True

    def mtm(self, p: float) -> float:
        if not self.in_pool:
            return self.flat_cash + self.fees_open
        return position_value(self.L, self.pa, self.pb, p) + self.fees_open

    def hodl(self, p: float) -> float:
        return self.hodl_sol * p + self.hodl_usdc

    def recenter(self, trig: float, full_width_pct: float, *, autoswap: bool = True) -> None:
        if not self.in_pool:
            return
        eq = position_value(self.L, self.pa, self.pb, trig)
        self.gas += GAS_PER_RECENTER_USD
        self.n_rebals += 1
        redeploy = max(eq + self.fees_open - GAS_PER_RECENTER_USD, 1.0)
        self.fees_tot += self.fees_open
        self.fees_open = 0.0
        self.bot_vol += eq + redeploy
        if not autoswap:
            # One-sided: keep inventory mark, open new band around trig without forcing 50/50.
            # Approximated by redeploying full equity into the new band (same as autoswap for MTM;
            # the difference is we skip an extra round-trip fee — already not modeled).
            pass
        self.pa, self.pb = band_bounds(trig, full_width_pct)
        self.L = liquidity_from_capital(redeploy, self.pa, self.pb, trig)

    def exit_to_hold(self, p: float) -> None:
        if not self.in_pool:
            return
        self.flat_cash = position_value(self.L, self.pa, self.pb, p) + self.fees_open
        self.fees_tot += self.fees_open
        self.fees_open = 0.0
        self.in_pool = False
        self.L = 0.0

    def enter_from_hold(self, p: float, full_width_pct: float) -> None:
        if self.in_pool:
            return
        capital = max(self.flat_cash, 1.0)
        self.flat_cash = 0.0
        self.in_pool = True
        self.pa, self.pb = band_bounds(p, full_width_pct)
        self.L = liquidity_from_capital(capital, self.pa, self.pb, p)
        self.bot_vol += capital


def _trailing_abs_return(closes: list[float], n: int) -> float:
    if len(closes) < n + 1 or closes[-n - 1] <= 0:
        return 0.0
    return abs(closes[-1] / closes[-n - 1] - 1.0)


def _trailing_vol(closes: list[float], n: int = 24) -> float:
    if len(closes) < n + 1:
        return 0.0
    rets = []
    for i in range(-n, 0):
        a, b = closes[i - 1], closes[i]
        if a > 0:
            rets.append(abs(b / a - 1.0))
    if not rets:
        return 0.0
    return sum(rets) / len(rets)


def run_replay(
    candles: list[Candle],
    cfg: RuleConfig,
    *,
    path_mode: str,
    conc: float,
    fee: float = POOL_FEE,
) -> ReplayResult:
    if not candles:
        raise ValueError("empty candles")
    p0 = candles[0].open
    pa, pb = band_bounds(p0, cfg.full_width_pct)
    book = Book(START_CAPITAL, pa, pb, p0)

    equity_path: list[float] = []
    hodl_path: list[float] = []
    closes: list[float] = []
    in_steps = 0
    total_steps = 0
    rebals_day: dict[str, int] = {}
    policy_pos: Optional[Position] = None
    rebalance_ts: list[float] = []

    for candle in candles:
        closes.append(candle.close)
        day = datetime.fromtimestamp(candle.ts, timezone.utc).strftime("%Y-%m-%d")
        rebals_day.setdefault(day, 0)

        if path_mode == "close":
            prices = close_only_path(candle.close)
            # Need open as previous mark for continuity — use prior close via book state.
            prices = [candle.open] + prices
        else:
            prices = intra_hour_path(candle.open, candle.high, candle.low, candle.close)

        steps_in = 0
        n_segments = max(len(prices) - 1, 1)

        for p in prices[1:]:
            total_steps += 1
            if cfg.name == "chop_gate":
                vol = _trailing_vol(closes, 24)
                quiet = vol <= cfg.vol_gate and _trailing_abs_return(closes, 24) <= cfg.trend_gate
                if quiet and not book.in_pool:
                    book.enter_from_hold(p, cfg.full_width_pct)
                if (not quiet) and book.in_pool:
                    book.exit_to_hold(p)
                    continue
                if not book.in_pool:
                    continue

            if not book.in_pool:
                continue

            thr = cfg.trigger_pct / 100.0
            lo = book.pa * (1.0 - thr)
            hi = book.pb * (1.0 + thr)

            if cfg.name == "sit_wide":
                if lo < p < hi:
                    steps_in += 1
                    in_steps += 1
                continue

            if cfg.name == "live_rebalancer":
                if lo < p < hi:
                    steps_in += 1
                    in_steps += 1
                    continue
                # hourly cap
                if cfg.hourly_cap is not None:
                    # approximate: count rebals in last hour via timestamps stored as ints of ts
                    recent = sum(1 for t in rebalance_ts if candle.ts - t <= 3600)
                    if recent >= cfg.hourly_cap:
                        continue
                trig = hi if p >= hi else lo
                book.recenter(trig, cfg.full_width_pct, autoswap=True)
                rebalance_ts.append(candle.ts)
                rebals_day[day] += 1
                continue

            if cfg.name == "do_not_chase":
                trending = _trailing_abs_return(closes, 24) >= cfg.trend_gate
                if lo < p < hi:
                    steps_in += 1
                    in_steps += 1
                    continue
                if trending:
                    # stay one-sided OOR — no autoswap recenter
                    continue
                if rebals_day[day] >= cfg.max_rebals_per_day:
                    continue
                # exhaustion-ish: only recenter if last hourly move is large vs recent
                if len(closes) >= 6:
                    body = closes[-6:-1]
                    last = abs(closes[-1] / closes[-2] - 1.0) if closes[-2] > 0 else 0.0
                    avg = sum(abs(body[i] / body[i - 1] - 1.0) for i in range(1, len(body)) if body[i - 1] > 0)
                    avg = avg / max(len(body) - 1, 1)
                    if avg > 0 and last < 2.5 * avg:
                        continue
                trig = hi if p >= hi else lo
                book.recenter(trig, cfg.full_width_pct, autoswap=False)
                rebals_day[day] += 1
                continue

            if cfg.name == "policy":
                # Convert full-width to logic half-width (logic uses ± half).
                half = cfg.full_width_pct / 2.0
                params = Params(
                    range_width_pct=_dec(half),
                    rebalance_trigger_pct=_dec(cfg.trigger_pct),
                    skew_bias=_dec(cfg.skew),
                    max_rebalances_per_hour=cfg.hourly_cap if cfg.hourly_cap is not None else 10_000,
                    exhaustion_return_z=_dec("3") if cfg.exhaustion else _dec("99"),
                    capital_allocation_usdc=_dec(START_CAPITAL),
                )
                # Build returns for exhaustion
                rets = []
                for i in range(1, min(len(closes), 13)):
                    if closes[-i - 1] > 0:
                        rets.append(_dec(closes[-i] / closes[-i - 1] - 1.0))
                rets = list(reversed(rets))
                mom = 0
                if len(closes) >= 5 and closes[-5] > 0:
                    d = closes[-1] / closes[-5] - 1.0
                    if abs(d) >= 0.001:
                        mom = 1 if d > 0 else -1
                snap = Snapshot(
                    ts=candle.ts,
                    spot=_dec(p),
                    equity_usdc=_dec(book.mtm(p)),
                    momentum_sign=mom,
                    recent_returns=rets,
                    rebalance_timestamps=rebalance_ts,
                )
                if policy_pos is None:
                    # seed from book bounds
                    policy_pos = Position(
                        lower=_dec(book.pa),
                        upper=_dec(book.pb),
                        center=_dec((book.pa + book.pb) / 2),
                        opened_at=candle.ts,
                        opened_equity=_dec(START_CAPITAL),
                    )
                # Sync policy bounds with book
                policy_pos.lower = _dec(book.pa)
                policy_pos.upper = _dec(book.pb)
                policy_pos.center = _dec((book.pa + book.pb) / 2)
                d = decide(params, snap, policy_pos)
                if d.action == Action.HOLD or d.action == Action.STOP:
                    if book.pa <= p <= book.pb:
                        steps_in += 1
                        in_steps += 1
                    continue
                if d.action in (Action.REBALANCE, Action.OPEN) and d.lower and d.upper:
                    if lo < p < hi and d.action != Action.OPEN:
                        steps_in += 1
                        in_steps += 1
                        continue
                    trig = p
                    book.recenter(trig, cfg.full_width_pct, autoswap=True)
                    # override band with decide() bounds (same width family)
                    book.pa = float(d.lower)
                    book.pb = float(d.upper)
                    eq = book.mtm(p) - book.fees_open
                    book.L = liquidity_from_capital(max(eq, 1.0), book.pa, book.pb, p)
                    rebalance_ts.append(candle.ts)
                    rebals_day[day] += 1
                    policy_pos = Position(
                        lower=d.lower,
                        upper=d.upper,
                        center=d.center or _dec(p),
                        opened_at=candle.ts,
                        opened_equity=_dec(book.mtm(p)),
                    )
                continue

            # fallback: treat as live
            if lo < p < hi:
                steps_in += 1
                in_steps += 1

        # accrue fees for fraction of hour in range
        if book.in_pool and steps_in > 0:
            eq = position_value(book.L, book.pa, book.pb, candle.close)
            book.fees_open += fee_on_volume(
                candle.volume * (steps_in / n_segments),
                eq,
                conc=conc,
                fee=fee,
            )

        equity_path.append(book.mtm(candle.close))
        hodl_path.append(book.hodl(candle.close))

    lp48 = window_deltas(equity_path, 48)
    h48 = window_deltas(hodl_path, 48)
    med_lp = median(lp48)
    med_h = median(h48)

    daily: list[dict[str, Any]] = []
    for i, candle in enumerate(candles):
        day = datetime.fromtimestamp(candle.ts, timezone.utc).strftime("%m-%d")
        row = {
            "day": day,
            "lp": round(equity_path[i], 1),
            "hodl": round(hodl_path[i], 1),
        }
        if not daily or daily[-1]["day"] != day:
            daily.append(row)
        else:
            daily[-1] = row

    return ReplayResult(
        rule=cfg.name,
        path=path_mode,
        conc=conc,
        full_width_pct=cfg.full_width_pct,
        trigger_pct=cfg.trigger_pct,
        hourly_cap=cfg.hourly_cap,
        end_equity=round(equity_path[-1], 2),
        end_hodl=round(hodl_path[-1], 2),
        fees=round(book.fees_tot + book.fees_open, 2),
        gas=round(book.gas, 2),
        n_rebals=book.n_rebals,
        in_range_pct=round(100.0 * in_steps / total_steps, 1) if total_steps else 0.0,
        median_48h_lp=round(med_lp, 2),
        median_48h_hodl=round(med_h, 2),
        median_48h_edge=round(med_lp - med_h, 2),
        bot_vol=round(book.bot_vol, 0),
        trend_gate=cfg.trend_gate,
        vol_gate=cfg.vol_gate,
        skew=cfg.skew,
        exhaustion=cfg.exhaustion,
        daily=daily,
    )


def baseline_ok(r: ReplayResult) -> tuple[bool, str]:
    lp_ok = abs(r.end_equity - BASELINE_LP_TARGET) <= BASELINE_TOL_LP
    hodl_ok = abs(r.end_hodl - BASELINE_HODL_TARGET) <= BASELINE_TOL_HODL
    ok = lp_ok and hodl_ok
    msg = (
        f"baseline live w=1.0 thr=0.05 path=highlow conc=20: "
        f"lp={r.end_equity} (target~{BASELINE_LP_TARGET}±{BASELINE_TOL_LP}) "
        f"hodl={r.end_hodl} (target~{BASELINE_HODL_TARGET}±{BASELINE_TOL_HODL})"
    )
    return ok, msg


def _num(v: Any, default: float = 0.0) -> float:
    if v is None:
        return default
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, str):
        try:
            return float(v)
        except ValueError:
            return default
    if isinstance(v, dict):
        for k in ("usd", "h24", "value", "amount", "tvl", "volume"):
            if k in v:
                return _num(v[k], default)
    return default


def screen_orca_sol_usdc() -> list[dict[str, Any]]:
    """Public Orca API — never invent addresses."""
    url = "https://api.orca.so/v2/solana/pools?tokens=SOL%2CUSDC&sort=tvl&size=50"
    req = urllib.request.Request(url, headers={"User-Agent": "hummingbot-hackathon-cup/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    pools = data.get("data") or data.get("pools") or []
    if isinstance(data, list):
        pools = data
    out = []
    for p in pools:
        if not isinstance(p, dict):
            continue
        addr = p.get("address") or p.get("pubkey") or p.get("whirlpool")
        if not addr:
            continue
        fee_rate = p.get("feeRate") or p.get("fee_rate") or p.get("lpFeeRate")
        fee_pct = None
        if fee_rate is not None:
            fr = _num(fee_rate)
            fee_pct = fr / 1_000_000.0 if fr > 1 else fr
            if fr > 10:
                fee_pct = fr / 1_000_000.0
        tvl = _num(p.get("tvlUsdc") or p.get("tvl") or p.get("liquidity"))
        vol = _num(p.get("volumeUsdc24h") or p.get("volume24h") or p.get("volume"))
        stats = p.get("stats")
        if isinstance(stats, dict):
            day = stats.get("24h") or stats.get("day") or {}
            if isinstance(day, dict):
                vol = _num(day.get("volume") or day.get("volumeUsdc"), vol)
            else:
                vol = _num(stats.get("volume") or stats.get("volume_24h"), vol)
        out.append(
            {
                "address": addr,
                "fee_rate_raw": fee_rate if not isinstance(fee_rate, dict) else str(fee_rate)[:80],
                "fee_pct": fee_pct,
                "tvl": tvl,
                "volume_24h": vol,
                "intensity": (vol / tvl) * fee_pct if tvl > 0 and fee_pct else None,
                "source": "orca_api",
            }
        )
    return out


def gecko_screen() -> list[dict[str, Any]]:
    """Fallback: GeckoTerminal Orca SOL/USDC pools."""
    url = (
        "https://api.geckoterminal.com/api/v2/networks/solana/dexes/orca/"
        "pools?page=1"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "hummingbot-hackathon-cup/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode())
    out = []
    for item in data.get("data") or []:
        attrs = item.get("attributes") or {}
        name = (attrs.get("name") or "").upper()
        if "SOL" not in name or "USDC" not in name:
            continue
        addr = attrs.get("address")
        if not addr:
            continue
        tvl = float(attrs.get("reserve_in_usd") or 0)
        vol = float((attrs.get("volume_usd") or {}).get("h24") or 0)
        # fee unknown from this endpoint — leave None
        out.append(
            {
                "address": addr,
                "name": attrs.get("name"),
                "fee_pct": None,
                "tvl": tvl,
                "volume_24h": vol,
                "intensity": None,
                "source": "geckoterminal",
            }
        )
    return out


def build_grid_configs() -> list[RuleConfig]:
    cfgs: list[RuleConfig] = []
    widths = [1.0, 2.0, 4.0, 8.0, 16.0]
    triggers = [0.05, 0.5, 1.5, 3.0]
    caps = [None, 2, 6]
    for w in widths:
        for t in triggers:
            for cap in caps:
                cfgs.append(RuleConfig("live_rebalancer", w, t, cap))
                for skew in (0.5, 0.6):
                    for exh in (False, True):
                        cfgs.append(
                            RuleConfig(
                                "policy",
                                w,
                                t,
                                cap,
                                skew=skew,
                                exhaustion=exh,
                            )
                        )
    for w in (8.0, 16.0):
        cfgs.append(RuleConfig("sit_wide", w, 0.05, None))
    for w in (4.0, 8.0):
        for trend in (0.02, 0.04):
            cfgs.append(
                RuleConfig(
                    "do_not_chase",
                    w,
                    0.5,
                    None,
                    trend_gate=trend,
                    max_rebals_per_day=2,
                )
            )
    for w in (4.0, 8.0):
        for vg in (0.008, 0.015):
            cfgs.append(RuleConfig("chop_gate", w, 0.05, None, vol_gate=vg, trend_gate=0.03))
    return cfgs


def evaluate_promotion(
    train_rows: list[ReplayResult],
    hold_rows: list[ReplayResult],
) -> dict[str, Any]:
    """Promote only if holdout 1x edge > 0 on both paths."""
    # group hold by key
    def key(r: ReplayResult) -> tuple:
        return (
            r.rule,
            r.full_width_pct,
            r.trigger_pct,
            r.hourly_cap,
            r.path,
            r.conc,
            r.trend_gate,
            r.vol_gate,
            r.skew,
            r.exhaustion,
        )

    hold_map = {key(r): r for r in hold_rows}
    train_1x = [r for r in train_rows if r.conc == 1.0 and r.path == "highlow"]
    train_1x.sort(key=lambda r: r.median_48h_edge, reverse=True)

    candidates = []
    for tr in train_1x:
        h_hl = hold_map.get(
            (tr.rule, tr.full_width_pct, tr.trigger_pct, tr.hourly_cap, "highlow", 1.0, tr.trend_gate, tr.vol_gate, tr.skew, tr.exhaustion)
        )
        h_cl = hold_map.get(
            (tr.rule, tr.full_width_pct, tr.trigger_pct, tr.hourly_cap, "close", 1.0, tr.trend_gate, tr.vol_gate, tr.skew, tr.exhaustion)
        )
        if not h_hl or not h_cl:
            continue
        ok = h_hl.median_48h_edge > 0 and h_cl.median_48h_edge > 0
        h20 = hold_map.get(
            (tr.rule, tr.full_width_pct, tr.trigger_pct, tr.hourly_cap, "highlow", 20.0, tr.trend_gate, tr.vol_gate, tr.skew, tr.exhaustion)
        )
        win_20_hl = bool(h20 and h20.median_48h_edge > 0)
        reject = rejects_200x_only(ok, win_20_hl, True) if not ok else False
        candidates.append(
            {
                "train_edge": tr.median_48h_edge,
                "hold_highlow_edge": h_hl.median_48h_edge,
                "hold_close_edge": h_cl.median_48h_edge,
                "promote": ok,
                "rejected_200x_only": reject,
                "config": {
                    "rule": tr.rule,
                    "full_width_pct": tr.full_width_pct,
                    "trigger_pct": tr.trigger_pct,
                    "hourly_cap": tr.hourly_cap,
                    "trend_gate": tr.trend_gate,
                    "vol_gate": tr.vol_gate,
                    "skew": tr.skew,
                    "exhaustion": tr.exhaustion,
                },
                "hold_highlow": asdict(h_hl),
                "hold_close": asdict(h_cl),
            }
        )
    promoted = [c for c in candidates if c["promote"]]
    promoted.sort(
        key=lambda c: min(c["hold_highlow_edge"], c["hold_close_edge"]),
        reverse=True,
    )
    return {
        "n_train_ranked": len(train_1x),
        "n_candidates_checked": len(candidates),
        "promoted": promoted[:5],
        "decision": "PROMOTE" if promoted else "NO_PROMOTE",
        "top_train_even_if_rejected": [
            {
                "rule": r.rule,
                "full_width_pct": r.full_width_pct,
                "trigger_pct": r.trigger_pct,
                "hourly_cap": r.hourly_cap,
                "train_edge": r.median_48h_edge,
                "end_equity": r.end_equity,
                "end_hodl": r.end_hodl,
            }
            for r in train_1x[:10]
        ],
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument(
        "--ohlcv",
        type=Path,
        default=ROOT / "data" / "solusdc_ohlcv_hourly.json",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "cup_grid_20260928.json",
    )
    ap.add_argument("--skip-screen", action="store_true")
    ap.add_argument("--quick", action="store_true", help="Tiny subset for smoke")
    args = ap.parse_args()

    candles = load_hourly_candles(args.ohlcv)
    # Keep last 21d aligned with canvas
    candles = candles[-21 * 24 :]
    train = [c for c in candles if c.ts < TRAIN_END_TS]
    hold = [c for c in candles if c.ts >= TRAIN_END_TS]
    nap = napkin()

    print(json.dumps({"napkin": asdict(nap), "n_train": len(train), "n_hold": len(hold)}, indent=2))

    # Baseline check (full window, highlow, conc 20) — matches canvas
    base_cfg = RuleConfig("live_rebalancer", 1.0, 0.05, None)
    base = run_replay(candles, base_cfg, path_mode="highlow", conc=20.0)
    ok, base_msg = baseline_ok(base)
    print(base_msg, "PASS" if ok else "FAIL")
    if not ok:
        # still continue but flag — engine must be close
        print("WARNING: baseline drift; investigate before trusting promotes")

    configs = build_grid_configs()
    if args.quick:
        configs = [
            RuleConfig("live_rebalancer", 1.0, 0.05, None),
            RuleConfig("sit_wide", 16.0, 0.05, None),
            RuleConfig("do_not_chase", 8.0, 0.5, None, trend_gate=0.03),
            RuleConfig("chop_gate", 8.0, 0.05, None, vol_gate=0.012),
            RuleConfig("policy", 4.0, 1.5, 2, skew=0.5, exhaustion=True),
        ]

    paths = ("highlow", "close")
    concs = (1.0, 20.0)
    train_rows: list[ReplayResult] = []
    hold_rows: list[ReplayResult] = []
    n = 0
    total = len(configs) * len(paths) * len(concs)
    for cfg in configs:
        for path_mode in paths:
            for conc in concs:
                n += 1
                if n % 25 == 0 or n == total:
                    print(f"progress {n}/{total}", flush=True)
                train_rows.append(run_replay(train, cfg, path_mode=path_mode, conc=conc))
                hold_rows.append(run_replay(hold, cfg, path_mode=path_mode, conc=conc))

    promo = evaluate_promotion(train_rows, hold_rows)

    # Pool screen
    screen: dict[str, Any] = {"pools": [], "higher_tier_candidates": [], "error": None}
    if not args.skip_screen:
        try:
            pools = screen_orca_sol_usdc()
            if not pools:
                pools = gecko_screen()
            screen["pools"] = pools[:30]
            base_intensity = nap.fee_intensity_full_liquidity
            for p in pools:
                inten = p.get("intensity")
                fee_pct = p.get("fee_pct")
                tvl = p.get("tvl") or 0
                vol = p.get("volume_24h") or 0
                if fee_pct and tvl > 0:
                    inten = (vol / tvl) * fee_pct
                    p["intensity"] = inten
                if inten is not None and inten > base_intensity and p.get("address") != POOL_ADDRESS:
                    if fee_pct and fee_pct > POOL_FEE:
                        screen["higher_tier_candidates"].append(p)
            # SitWide replay on higher tier only if we have fee + we cannot get OHLCV easily —
            # record intensity only; do not invent candles.
            screen["note"] = (
                "Higher-tier SitWide needs that pool's OHLCV. "
                "Candidates listed by intensity only; no invented addresses."
            )
        except Exception as e:
            screen["error"] = str(e)

    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "pool": POOL_ADDRESS,
        "napkin": asdict(nap),
        "baseline": {
            "ok": ok,
            "message": base_msg,
            "result": asdict(base),
        },
        "train_end": "2026-09-21T00:00:00+00:00",
        "n_configs": len(configs),
        "promotion": promo,
        "pool_screen": screen,
        "train_rows_sample": [asdict(r) for r in sorted(train_rows, key=lambda x: -x.median_48h_edge)[:20]],
        "hold_rows_sample": [asdict(r) for r in sorted(hold_rows, key=lambda x: -x.median_48h_edge)[:20]],
        "all_train_1x_highlow": [
            asdict(r)
            for r in sorted(
                [x for x in train_rows if x.conc == 1.0 and x.path == "highlow"],
                key=lambda x: -x.median_48h_edge,
            )
        ],
        "all_hold_1x_highlow": [
            asdict(r)
            for r in sorted(
                [x for x in hold_rows if x.conc == 1.0 and x.path == "highlow"],
                key=lambda x: -x.median_48h_edge,
            )
        ],
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    # Strip bulky daily from all_* to keep file smaller — keep in samples only
    for section in ("all_train_1x_highlow", "all_hold_1x_highlow"):
        for row in payload[section]:
            row.pop("daily", None)
    args.out.write_text(json.dumps(payload, indent=2) + "\n")
    print(
        json.dumps(
            {
                "out": str(args.out),
                "decision": promo["decision"],
                "n_promoted": len(promo["promoted"]),
                "baseline_ok": ok,
                "higher_tier_n": len(screen.get("higher_tier_candidates") or []),
            },
            indent=2,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
