#!/usr/bin/env python3
"""R004b — "Flush and fade" on Czfq: USDC by default; after a high-volume
flush, buy SOL and sell the bounce through a SOL-only Orca band that earns
swap fees on the way up. Hard stop and time stop. Optional chop LP between
events. Parameters chosen on pre-Cup bars only; Cup and post-Cup are holdouts.
"""

from __future__ import annotations

import itertools
import json
import math
import statistics
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

import cup_alpha_replay as R

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "research" / "artifacts" / "r004_flush_bounce.json"


@dataclass(frozen=True)
class Flush:
    lookback: int = 36  # bars (5m) for the flush return
    drop: float = 3.0  # % drop over lookback that counts as a flush
    vol_mult: float = 2.0  # lookback volume vs trailing-day median of same span
    confirm: float = 0.3  # % above the post-flush low before buying
    band_lo: float = 0.5  # % above entry where the sell band starts
    band_w: float = 3.0  # band width %
    stop: float = 2.0  # % below entry
    tmax: int = 144  # bars max hold
    frac: float = 1.0  # share of book used
    chop_w: float = 0.0  # >0: tight centered LP between events when calm
    chop_tau: float = 0.3


@dataclass
class Out:
    ret_pct: float
    fees: float
    fee_volume: float
    trades: int
    wins: int
    max_dd_pct: float
    curve: list
    log: list


_SERIES: dict[int, tuple] = {}


def _series(bars):
    key = id(bars)
    if key not in _SERIES:
        closes = [b[4] for b in bars]
        cv = [0.0]
        for b in bars:
            cv.append(cv[-1] + b[5])
        _SERIES[key] = (closes, R.ema(closes, 12), R.ema(closes, 96), cv)
    return _SERIES[key]


def run(cfg: Flush, bars, i0: int, i1: int, k: float) -> Out:
    closes, ef, es, cv = _series(bars)
    book = R.Book(R.CAPITAL)
    state = "flat"
    entry = low = 0.0
    t_in = 0
    trades = wins = 0
    eq_in = 0.0
    peak, mdd = R.CAPITAL, 0.0
    curve = []
    log = []
    span = cfg.lookback
    armed_low = None
    for i in range(i0, i1):
        t, o, h, lo, c, v = bars[i]
        if book.L > 0:
            f = k * book.L * v * R.overlap(lo, h, book.pa, book.pb)
            book.fees += f
            book.usdc += f

        if state in ("flat", "chop"):
            ret = (c / closes[i - span] - 1) * 100
            vsum = cv[i + 1] - cv[i + 1 - span]
            ref = [cv[j + 1] - cv[j + 1 - span] for j in range(i - 288, i - span, span)]
            vref = statistics.median(ref) if ref else vsum
            if ret <= -cfg.drop and vsum >= cfg.vol_mult * vref:
                armed_low = min(lo, armed_low) if armed_low else lo
            if armed_low is not None:
                armed_low = min(armed_low, lo)
                if c >= armed_low * (1 + cfg.confirm / 100):
                    book.close_lp(c)
                    eq_in = book.equity(c)
                    book.swap_to(eq_in * cfg.frac, c)
                    entry, t_in = c, i
                    pa = c * (1 + cfg.band_lo / 100)
                    pb = pa * (1 + cfg.band_w / 100)
                    sol_avail = book.sol
                    L = sol_avail / (1 / math.sqrt(pa) - 1 / math.sqrt(pb))
                    book.sol -= sol_avail
                    book.L, book.pa, book.pb = L, pa, pb
                    book.usdc -= R.GAS_PER_TX
                    book.n_rebal += 1
                    state, armed_low = "long", None
                    trades += 1
                elif (closes[i] / closes[i - 288] - 1) * 100 > 2 * cfg.drop:
                    armed_low = None

            if state != "long" and cfg.chop_w > 0:
                gap = (ef[i] / es[i] - 1) * 100
                calm = abs(gap) < cfg.chop_tau and armed_low is None
                if calm:
                    if book.L <= 0 or c < book.pa or c > book.pb:
                        book.close_lp(c)
                        half = cfg.chop_w / 200
                        book.open_lp(c, c * (1 - half), c * (1 + half))
                    state = "chop"
                elif state == "chop":
                    book.close_lp(c)
                    book.swap_to(0.0, c)
                    state = "flat"

        elif state == "long":
            done = c >= book.pb or c <= entry * (1 - cfg.stop / 100) or i - t_in >= cfg.tmax
            if done:
                book.close_lp(c)
                book.swap_to(0.0, c)
                wins += book.equity(c) > eq_in
                why = "target" if c >= book.pb else ("stop" if c <= entry * (1 - cfg.stop / 100) else "time")
                log.append({"t_in": bars[t_in][0], "entry": entry, "t_out": t, "exit": c,
                            "pnl_pct": (book.equity(c) / eq_in - 1) * 100, "why": why})
                state = "flat"

        eq = book.equity(c)
        curve.append(eq)
        peak = max(peak, eq)
        mdd = max(mdd, (peak - eq) / peak)

    end = book.equity(closes[i1 - 1])
    if state == "long":
        log.append({"t_in": bars[t_in][0], "entry": entry, "t_out": bars[i1 - 1][0], "exit": closes[i1 - 1],
                    "pnl_pct": (end / eq_in - 1) * 100, "why": "open_at_window_end"})
    return Out((end / R.CAPITAL - 1) * 100, book.fees, book.fees / R.POOL_FEE, trades, wins, mdd * 100, curve, log)


def main() -> int:
    bars = R.load_bars()
    i_tr0 = 300
    i_c0, i_c1 = R.idx(bars, R.CUP_START), R.idx(bars, R.CUP_END)
    wins = {"train_pre_cup": (i_tr0, i_c0), "cup_48h": (i_c0, i_c1), "post_cup": (i_c1, len(bars))}
    grid = list(
        itertools.product(
            [24, 36, 72],  # lookback 2h / 3h / 6h
            [2.0, 3.0, 4.0],  # drop %
            [1.5, 2.0, 3.0],  # vol multiple
            [0.3, 0.8],  # confirm %
            [0.0, 0.5],  # band start above entry
            [2.0, 3.0, 5.0],  # band width
            [1.5, 2.5, 4.0],  # stop
            [144, 288],  # time stop
        )
    )
    results = []
    for g in grid:
        cfg = Flush(*g)
        tr = run(cfg, bars, *wins["train_pre_cup"], R.K_PRE_CUP)
        results.append((cfg, tr))
    # Train objective: return, need >=2 trades, penalise drawdown
    eligible = [x for x in results if x[1].trades >= 2]
    eligible.sort(key=lambda x: x[1].ret_pct - 0.5 * x[1].max_dd_pct, reverse=True)
    top = eligible[:10]

    report = {"n_grid": len(grid), "n_eligible": len(eligible), "top": []}
    print(f"grid {len(grid)} eligible(>=2 train trades) {len(eligible)}")
    for cfg, tr in top:
        row = {"cfg": asdict(cfg)}
        for name, (a, b) in wins.items():
            o = run(cfg, bars, a, b, R.K_PRE_CUP)
            row[name] = {k: v for k, v in asdict(o).items() if k not in ("curve",)}
            if name == "cup_48h":
                step = max(1, len(o.curve) // 96)
                row["cup_curve"] = [round(x, 2) for x in o.curve[::step]]
        report["top"].append(row)
        print(
            f"lb{cfg.lookback} d{cfg.drop} vm{cfg.vol_mult} cf{cfg.confirm} bl{cfg.band_lo} bw{cfg.band_w} st{cfg.stop} tm{cfg.tmax} | "
            + " | ".join(
                f"{n[:5]} {row[n]['ret_pct']:+5.2f}% t{row[n]['trades']}/{row[n]['wins']} fees${row[n]['fees']:.2f}"
                for n in wins
            )
        )
    # Robustness: distribution of cup / post returns across all eligible configs
    cup_rets, post_rets = [], []
    for cfg, _ in eligible:
        cup_rets.append(run(cfg, bars, *wins["cup_48h"], R.K_PRE_CUP).ret_pct)
        post_rets.append(run(cfg, bars, *wins["post_cup"], R.K_PRE_CUP).ret_pct)
    def dist(xs):
        xs = sorted(xs)
        return {"n": len(xs), "p10": xs[len(xs) // 10], "median": xs[len(xs) // 2], "p90": xs[9 * len(xs) // 10],
                "share_pos": sum(x > 0 for x in xs) / len(xs)}
    report["eligible_cup"] = dist(cup_rets)
    report["eligible_post"] = dist(post_rets)
    print("eligible cup dist", report["eligible_cup"])
    print("eligible post dist", report["eligible_post"])
    OUT.write_text(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
