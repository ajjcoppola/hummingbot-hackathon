#!/usr/bin/env python3
"""R004 — regime In/Out market-making replay on real Czfq 5-minute candles.

Fees are calibrated from our own on-chain LP fee accrual (R003m pre-Cup,
S001 during Cup): fee_bar = k * L * volume_bar * overlap(bar range, band).
Parameters are chosen on pre-Cup data only (train), then scored on the Cup
window and the week after (holdouts). Research only — promotion means porting
the winning rule into src/orca_tight_range/logic.py decide().
"""

from __future__ import annotations

import argparse
import itertools
import json
import math
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BARS_PATH = ROOT / "research" / "artifacts" / "czfq_5m.json"
OUT_PATH = ROOT / "research" / "artifacts" / "r004_results.json"

POOL_FEE = 0.0004
SWAP_COST = 0.0005  # pool fee + slippage on swapped notional
GAS_PER_TX = 0.005  # USD; close/open/swap each count as one tx
K_PRE_CUP = 1.2057e-11  # R003m 2026-09-29..10-02 fee per (L * USD volume)
K_CUP = 1.8640e-11  # S001 inside the Cup window (sensitivity only)
CAPITAL = 800.0

CUP_START = datetime(2026, 10, 7, 2, 0, tzinfo=timezone.utc).timestamp()
CUP_END = datetime(2026, 10, 9, 2, 0, tzinfo=timezone.utc).timestamp()


def ts(s: str) -> float:
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()


def load_bars() -> list[tuple[float, float, float, float, float, float]]:
    rows = json.loads(BARS_PATH.read_text())
    return [tuple(float(x) for x in r) for r in rows]


def liquidity(capital: float, pa: float, pb: float, p: float) -> float:
    sp, spa, spb = math.sqrt(p), math.sqrt(pa), math.sqrt(pb)
    denom = (1.0 / sp - 1.0 / spb) * p + (sp - spa)
    return capital / denom if denom > 0 else 0.0


def amounts(L: float, pa: float, pb: float, p: float) -> tuple[float, float]:
    sp, spa, spb = math.sqrt(p), math.sqrt(pa), math.sqrt(pb)
    if p <= pa:
        return L * (1.0 / spa - 1.0 / spb), 0.0
    if p >= pb:
        return 0.0, L * (spb - spa)
    return L * (1.0 / sp - 1.0 / spb), L * (sp - spa)


def overlap(lo: float, hi: float, pa: float, pb: float) -> float:
    if hi <= lo:
        return 1.0 if pa <= lo <= pb else 0.0
    return max(0.0, min(hi, pb) - max(lo, pa)) / (hi - lo)


def ema(xs: list[float], n: int) -> list[float]:
    a = 2.0 / (n + 1.0)
    out, e = [], xs[0]
    for x in xs:
        e = a * x + (1 - a) * e
        out.append(e)
    return out


def rolling_vol(closes: list[float], n: int) -> list[float]:
    rets = [0.0] + [math.log(closes[i] / closes[i - 1]) for i in range(1, len(closes))]
    out, s, s2 = [], 0.0, 0.0
    for i, r in enumerate(rets):
        s += r
        s2 += r * r
        if i >= n:
            s -= rets[i - n]
            s2 -= rets[i - n] ** 2
        m = min(i + 1, n)
        var = max(0.0, s2 / m - (s / m) ** 2)
        out.append(math.sqrt(var))
    return out


@dataclass(frozen=True)
class Rule:
    name: str
    kind: str  # naked | victor | hoang | regime
    width: float = 16.0  # full width %
    fast: int = 6
    slow: int = 48
    tau: float = 0.3  # % gap fast vs slow EMA that counts as trend
    vol_cap: float = 9.9  # 5m vol % above which we stand aside
    up_mode: str = "sol"  # regime: what to hold in an uptrend
    hold: int = 3  # bars a new regime must persist before acting
    vol_k: float = 0.0  # victor: width = vol_k * daily vol


@dataclass
class Result:
    rule: str
    start: float
    end: float
    ret_pct: float
    fees: float
    fee_volume: float
    swap_notional: float
    n_rebal: int
    pct_in_lp: float
    max_dd_pct: float


class Book:
    def __init__(self, usdc: float):
        self.usdc = usdc
        self.sol = 0.0
        self.L = 0.0
        self.pa = self.pb = 0.0
        self.fees = 0.0
        self.swap_notional = 0.0
        self.n_rebal = 0

    def lp_value(self, p: float) -> float:
        if self.L <= 0:
            return 0.0
        b, q = amounts(self.L, self.pa, self.pb, p)
        return b * p + q

    def equity(self, p: float) -> float:
        return self.usdc + self.sol * p + self.lp_value(p)

    def close_lp(self, p: float) -> None:
        if self.L <= 0:
            return
        b, q = amounts(self.L, self.pa, self.pb, p)
        self.sol += b
        self.usdc += q
        self.L = 0.0
        self.usdc -= GAS_PER_TX

    def swap_to(self, target_sol_usd: float, p: float) -> None:
        cur = self.sol * p
        d = target_sol_usd - cur
        if abs(d) < 1.0:
            return
        cost = abs(d) * SWAP_COST
        self.swap_notional += abs(d)
        if d > 0:
            self.usdc -= d + cost
            self.sol += d / p
        else:
            self.sol += d / p
            self.usdc += -d - cost
        self.usdc -= GAS_PER_TX

    def open_lp(self, p: float, pa: float, pb: float) -> None:
        cap = self.equity(p) - 2 * GAS_PER_TX
        L = liquidity(cap * 0.995, pa, pb, p)
        b, q = amounts(L, pa, pb, p)
        self.swap_to(b * p, p)
        L = min(L, liquidity(self.equity(p) * 0.995, pa, pb, p))
        b, q = amounts(L, pa, pb, p)
        b = min(b, self.sol)
        q = min(q, self.usdc)
        self.sol -= b
        self.usdc -= q
        self.L, self.pa, self.pb = L, pa, pb
        self.usdc -= GAS_PER_TX
        self.n_rebal += 1


def simulate(rule: Rule, bars, i0: int, i1: int, k: float, sig) -> tuple[Result, list[float]]:
    closes = [b[4] for b in bars]
    efast, eslow, vol = sig
    book = Book(CAPITAL)
    p0 = closes[i0]
    curve = []
    regime, pending, pend_n = "flat", None, 0
    lp_bars = 0
    peak, mdd = CAPITAL, 0.0
    for i in range(i0, i1):
        t, o, h, lo, c, v = bars[i]
        if book.L > 0:
            f = k * book.L * v * overlap(lo, h, book.pa, book.pb)
            book.fees += f
            book.usdc += f
            lp_bars += 1
        gap = (efast[i] / eslow[i] - 1.0) * 100.0
        vv = vol[i] * 100.0

        if rule.kind == "naked":
            want = "lp"
        elif rule.kind == "victor":
            want = "flat" if vv > rule.vol_cap else "lp"
        elif rule.kind == "hoang":
            want = "lp_down" if gap < -rule.tau else ("lp_up" if gap > rule.tau else "lp")
        else:
            if vv > rule.vol_cap:
                want = "flat"
            elif gap < -rule.tau:
                want = "flat"
            elif gap > rule.tau:
                want = rule.up_mode
            else:
                want = "lp"

        if want != regime:
            if want == pending:
                pend_n += 1
            else:
                pending, pend_n = want, 1
            if pend_n >= rule.hold:
                regime = want
                book.close_lp(c)
                if regime == "flat":
                    book.swap_to(0.0, c)
                elif regime == "sol":
                    book.swap_to(book.equity(c) - 2 * GAS_PER_TX, c)
                pending, pend_n = None, 0
        else:
            pending, pend_n = None, 0

        lp_states = ("lp", "lp_up", "lp_down", "lpw")
        if regime in lp_states:
            w = rule.width
            if rule.kind == "victor":
                daily = vol[i] * math.sqrt(288) * 100.0
                w = max(2.0, min(30.0, rule.vol_k * daily))
            buf = 0.005 if rule.kind == "naked" else 0.0
            out_of_band = book.L <= 0 or c < book.pa * (1 - buf) or c > book.pb * (1 + buf)
            if out_of_band:
                book.close_lp(c)
                half = w / 200.0
                if regime == "lp_down":
                    pa, pb = c * (1 - 1.5 * half), c * (1 + 0.5 * half)
                elif regime == "lp_up":
                    pa, pb = c * (1 - 0.5 * half), c * (1 + 1.5 * half)
                else:
                    pa, pb = c * (1 - half), c * (1 + half)
                book.open_lp(c, pa, pb)

        eq = book.equity(c)
        curve.append(eq)
        peak = max(peak, eq)
        mdd = max(mdd, (peak - eq) / peak)

    end = book.equity(closes[i1 - 1])
    res = Result(
        rule=rule.name,
        start=bars[i0][0],
        end=bars[i1 - 1][0],
        ret_pct=(end / CAPITAL - 1) * 100,
        fees=book.fees,
        fee_volume=book.fees / POOL_FEE,
        swap_notional=book.swap_notional,
        n_rebal=book.n_rebal,
        pct_in_lp=lp_bars / max(1, i1 - i0) * 100,
        max_dd_pct=mdd * 100,
    )
    return res, curve


def idx(bars, t: float) -> int:
    for i, b in enumerate(bars):
        if b[0] >= t:
            return i
    return len(bars)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--k", choices=["pre", "cup"], default="pre")
    args = ap.parse_args()
    k = K_PRE_CUP if args.k == "pre" else K_CUP

    bars = load_bars()
    closes = [b[4] for b in bars]
    warm = 300
    i_train0 = warm
    i_cup0, i_cup1 = idx(bars, CUP_START), idx(bars, CUP_END)
    i_post1 = len(bars)
    windows = {
        "train_pre_cup": (i_train0, i_cup0),
        "cup_48h": (i_cup0, i_cup1),
        "post_cup": (i_cup1, i_post1),
    }

    sig_cache: dict[tuple[int, int, int], tuple] = {}

    def sig(fast: int, slow: int, vn: int = 24):
        key = (fast, slow, vn)
        if key not in sig_cache:
            sig_cache[key] = (ema(closes, fast), ema(closes, slow), rolling_vol(closes, vn))
        return sig_cache[key]

    def run(rule: Rule, win: str):
        a, b = windows[win]
        return simulate(rule, bars, a, b, k, sig(rule.fast, rule.slow))

    candidates: list[Rule] = [Rule("naked_16", "naked", width=16.0)]
    for w, vc, vk in itertools.product([8.0, 16.0], [0.25, 0.35, 0.5], [0.0, 2.0, 3.0]):
        kind_w = w if vk == 0 else 0
        candidates.append(Rule(f"victor_w{w:g}_vc{vc}_vk{vk:g}", "victor", width=w, vol_cap=vc, vol_k=vk))
    for w, f, s, tau in itertools.product([8.0, 16.0], [6, 12], [48, 144], [0.2, 0.5]):
        candidates.append(Rule(f"hoang_w{w:g}_{f}_{s}_t{tau}", "hoang", width=w, fast=f, slow=s, tau=tau))
    for w, f, s, tau, vc, up, hold in itertools.product(
        [1.0, 2.0, 3.0, 5.0, 8.0],
        [3, 6, 12],
        [24, 48, 96, 288],
        [0.1, 0.2, 0.35, 0.5, 0.8],
        [0.2, 0.35, 9.9],
        ["sol", "lp"],
        [1, 3],
    ):
        if f >= s:
            continue
        candidates.append(
            Rule(f"regime_w{w:g}_{f}_{s}_t{tau}_vc{vc}_{up}_h{hold}", "regime",
                 width=w, fast=f, slow=s, tau=tau, vol_cap=vc, up_mode=up, hold=hold)
        )

    train = []
    for r in candidates:
        res, _ = run(r, "train_pre_cup")
        train.append((r, res))

    def best(kind: str, n: int = 1):
        rows = [x for x in train if x[0].kind == kind]
        rows.sort(key=lambda x: x[1].ret_pct - 0.25 * x[1].max_dd_pct, reverse=True)
        return rows[:n]

    picks = [x[0] for x in best("naked")] + [x[0] for x in best("victor")] + [x[0] for x in best("hoang")]
    regime_top = best("regime", 5)
    picks += [x[0] for x in regime_top]
    always = [Rule("hold_usdc", "regime", tau=-1)]  # placeholder name for report

    report = {"k": k, "k_label": args.k, "n_candidates": len(candidates), "windows": {}, "picks": [asdict(p) for p in picks]}
    for win in windows:
        rows = []
        for r in picks:
            res, curve = run(r, win)
            row = asdict(res)
            row["kind"] = r.kind
            if win == "cup_48h":
                step = max(1, len(curve) // 96)
                row["curve"] = [round(x, 2) for x in curve[::step]]
            rows.append(row)
        a, b = windows[win]
        sol_ret = (closes[b - 1] / closes[a] - 1) * 100
        report["windows"][win] = {
            "from": datetime.fromtimestamp(bars[a][0], timezone.utc).isoformat(),
            "to": datetime.fromtimestamp(bars[b - 1][0], timezone.utc).isoformat(),
            "sol_ret_pct": sol_ret,
            "hodl_5050_pct": sol_ret / 2,
            "rows": rows,
        }

    # In-sample ceiling on the Cup itself (overfit, disclosed as such)
    cup_is = []
    for r in candidates:
        if r.kind != "regime":
            continue
        res, _ = run(r, "cup_48h")
        cup_is.append((r, res))
    cup_is.sort(key=lambda x: x[1].ret_pct, reverse=True)
    report["cup_in_sample_ceiling"] = [dict(asdict(res), params=asdict(r)) for r, res in cup_is[:3]]

    # Regime robustness: share of regime candidates profitable per window
    prof = {}
    for win in windows:
        n_pos = 0
        n = 0
        for r in candidates:
            if r.kind != "regime":
                continue
            res, _ = run(r, win)
            n += 1
            n_pos += res.ret_pct > 0
        prof[win] = {"n": n, "share_profitable": n_pos / n}
    report["regime_profitable_share"] = prof

    OUT_PATH.write_text(json.dumps(report, indent=2))
    for win, w in report["windows"].items():
        print(f"\n== {win}  {w['from'][:16]} -> {w['to'][:16]}  SOL {w['sol_ret_pct']:+.2f}%  50/50 {w['hodl_5050_pct']:+.2f}%")
        for row in w["rows"]:
            print(f"  {row['rule'][:44]:44s} ret {row['ret_pct']:+7.2f}%  fees ${row['fees']:7.2f}  "
                  f"vol ${row['fee_volume']:>9,.0f}  inLP {row['pct_in_lp']:5.1f}%  dd {row['max_dd_pct']:5.2f}%  rebal {row['n_rebal']}")
    print("\nCup in-sample ceiling (overfit):")
    for c in report["cup_in_sample_ceiling"]:
        print(f"  {c['rule']}  {c['ret_pct']:+.2f}%  fees ${c['fees']:.2f}")
    print("\nshare of regime candidates profitable:", json.dumps(prof))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
