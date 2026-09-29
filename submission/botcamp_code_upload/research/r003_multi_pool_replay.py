#!/usr/bin/env python3
"""R003 — multi-pool sit-wide 16% replay + hysteresis switcher (true SOL-USDC).

IMPORTANT correction vs R002 pool_screen: ``tokens=SOL,USDC`` is an OR filter.
Pools listed there as higher-intensity (BofA2ViU, GTHKH8s8, AfrddTGY, 77xSiQHX)
are NOT SOL-USDC (SOL-PUMP, ZEC-USDC, SOL-STONK, NEAR-USDC). This run uses
``tokensBothOf=SOL,USDC`` only. Addresses always come from the Orca API.

Hard filter (plan): TVL ≥ $500k, fee ≤ 1%, age > 30d. As of 2026-09-28 only
``Czfq3xZZ…`` clears TVL among true SOL-USDC tiers. Micro tiers are replayed
for research with an explicit thin-TVL caveat; they are not promotion candidates.

CAVEAT: TVL held constant at the snapshot value (no historical TVL).
Train 7–21 Sep 2026, holdout 21–28 Sep 2026.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "research"))
sys.path.insert(0, str(ROOT / "src"))

from cup_clmm_engine import (  # noqa: E402
    Candle,
    band_bounds,
    initial_mix,
    liquidity_from_capital,
    load_hourly_candles,
    position_value,
)
from orca_tight_range.pool_rank import (  # noqa: E402
    MIN_TVL_USD,
    PoolSnapshot,
    RankerState,
    decide_switch,
    filter_and_rank,
    snapshot_from_orca_row,
)

TRAIN_END_TS = datetime(2026, 9, 21, tzinfo=timezone.utc).timestamp()
START_CAPITAL = 800.0
FULL_WIDTH = 16.0
SWITCH_COST = 2.0 + 0.001 * START_CAPITAL
SOL = "So11111111111111111111111111111111111111112"
USDC = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
ORCA_POOLS = "https://api.orca.so/v2/solana/pools"


@dataclass
class SitResult:
    address: str
    label: str
    fee: float
    tvl: float
    window: str
    end_equity: float
    end_hodl: float
    fees: float
    edge: float
    n_bars: int
    passes_hard_filter: bool
    note: str = "constant_TVL_approx"


def fetch_true_sol_usdc() -> list[dict[str, Any]]:
    params = {
        "size": "50",
        "sortBy": "volume24h",
        "sortDirection": "desc",
        "stats": "24h,7d",
        "tokensBothOf": f"{SOL},{USDC}",
    }
    url = f"{ORCA_POOLS}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": "hummingbot-hackathon-r003/1.0"})
    with urllib.request.urlopen(req, timeout=45) as resp:
        payload = json.loads(resp.read().decode())
    rows = payload.get("data") or []
    if isinstance(rows, dict):
        rows = rows.get("pools") or []
    return list(rows)


def gecko_ohlcv(address: str, *, aggregate: int = 1, limit: int = 1000) -> list[Candle]:
    url = (
        f"https://api.geckoterminal.com/api/v2/networks/solana/pools/"
        f"{address}/ohlcv/hour?aggregate={aggregate}&limit={limit}&currency=usd"
    )
    req = urllib.request.Request(url, headers={"User-Agent": "hummingbot-hackathon-r003/1.0"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = json.loads(resp.read().decode())
    rows = raw["data"]["attributes"]["ohlcv_list"]
    bars = list(reversed(rows))
    out: list[Candle] = []
    for ts, o, h, l, c, vol in bars:
        out.append(
            Candle(ts=float(ts), open=float(o), high=float(h), low=float(l), close=float(c), volume=float(vol))
        )
    return out


def save_ohlcv(address: str, candles: list[Candle], dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "data": {
            "attributes": {
                "ohlcv_list": [
                    [c.ts, c.open, c.high, c.low, c.close, c.volume] for c in reversed(candles)
                ]
            }
        },
        "meta": {"address": address, "source": "geckoterminal", "fetched_note": "R003"},
    }
    dest.write_text(json.dumps(payload))


def sit_wide(
    candles: list[Candle],
    *,
    fee: float,
    tvl: float,
    capital: float = START_CAPITAL,
    full_width: float = FULL_WIDTH,
) -> tuple[float, float, float]:
    if not candles:
        return capital, capital, 0.0
    p0 = candles[0].close
    pa, pb = band_bounds(p0, full_width)
    L = liquidity_from_capital(capital, pa, pb, p0)
    base0, quote0 = initial_mix(L, pa, pb, p0)
    conc = 20.0 / full_width
    fees = 0.0
    for c in candles:
        share = min(1.0, (capital / tvl) * conc) if tvl > 0 else 0.0
        fees += c.volume * fee * share
    end_p = candles[-1].close
    end_eq = position_value(L, pa, pb, end_p) + fees
    end_hodl = base0 * end_p + quote0
    return end_eq, end_hodl, fees


def window_slice(candles: list[Candle], *, train: bool) -> list[Candle]:
    if train:
        return [c for c in candles if c.ts < TRAIN_END_TS]
    return [c for c in candles if c.ts >= TRAIN_END_TS]


def rolling_intensity(vols: list[float], idx: int, fee: float, tvl: float, window: int) -> float:
    if tvl <= 0 or idx < 0:
        return 0.0
    start = max(0, idx - window + 1)
    chunk = vols[start : idx + 1]
    if not chunk:
        return 0.0
    hours = len(chunk)
    daily = (sum(chunk) / hours) * 24.0 if hours else 0.0
    return (daily / tvl) * fee


def switcher_replay(
    series: dict[str, list[Candle]],
    meta: dict[str, dict[str, Any]],
    *,
    train: bool,
) -> dict[str, Any]:
    master_addr = next(iter(series))
    # Prefer Czfq as master clock if present
    for a in series:
        if a.startswith("Czfq"):
            master_addr = a
            break
    master = window_slice(series[master_addr], train=train)
    if not master:
        return {"error": "no_bars", "end_equity": START_CAPITAL}

    vol_map: dict[str, list[float]] = {}
    for addr, candles in series.items():
        w = window_slice(candles, train=train)
        vol_map[addr] = [c.volume for c in w]

    state = RankerState()
    equity = START_CAPITAL
    current_L = 0.0
    current_pa = current_pb = 0.0
    fees = 0.0
    switches = 0
    gas = 0.0

    for i, bar in enumerate(master):
        hours_left = max(0.0, (master[-1].ts - bar.ts) / 3600.0)
        pools_snap: list[PoolSnapshot] = []
        for addr, m in meta.items():
            if addr not in vol_map or i >= len(vol_map[addr]):
                continue
            vols = vol_map[addr]
            int24 = rolling_intensity(vols, i, m["fee"], m["tvl"], 24)
            int7d = rolling_intensity(vols, i, m["fee"], m["tvl"], 24 * 7)
            fee_pct = m["fee"] * 100.0
            tvl = m["tvl"]
            vol24 = (int24 / m["fee"]) * tvl if m["fee"] else 0.0
            vol7d = (int7d / m["fee"]) * tvl * 7.0 if m["fee"] else 0.0
            pools_snap.append(
                PoolSnapshot(
                    address=addr,
                    fee_pct=fee_pct,
                    tvl_usd=tvl,
                    volume_24h=vol24,
                    volume_7d=vol7d,
                    created_at="2023-01-01T00:00:00Z",
                )
            )
        decision, state = decide_switch(
            pools_snap,
            state,
            now_ts=bar.ts,
            equity=equity,
            hours_left=max(hours_left, 1.0),
        )
        px = bar.close
        if decision.action in ("open", "switch") and decision.target_address:
            if decision.action == "switch" and current_L > 0:
                equity = position_value(current_L, current_pa, current_pb, px) + fees
                fees = 0.0
                gas += SWITCH_COST
                switches += 1
            current_pa, current_pb = band_bounds(px, FULL_WIDTH)
            current_L = liquidity_from_capital(max(equity - fees, 1.0), current_pa, current_pb, px)
        if state.current_address and state.current_address in meta and current_L > 0:
            m = meta[state.current_address]
            conc = 20.0 / FULL_WIDTH
            tvl = m["tvl"]
            share = min(1.0, (equity / tvl) * conc) if tvl > 0 else 0.0
            fees += bar.volume * m["fee"] * share

    if current_L > 0:
        end_eq = position_value(current_L, current_pa, current_pb, master[-1].close) + fees - gas
    else:
        end_eq = equity - gas
    pa0, pb0 = band_bounds(master[0].close, FULL_WIDTH)
    L0 = liquidity_from_capital(START_CAPITAL, pa0, pb0, master[0].close)
    b0, q0 = initial_mix(L0, pa0, pb0, master[0].close)
    end_hodl = b0 * master[-1].close + q0
    return {
        "window": "train" if train else "holdout",
        "end_equity": end_eq,
        "end_hodl": end_hodl,
        "edge": end_eq - end_hodl,
        "fees": fees,
        "gas": gas,
        "switches": switches,
        "final_pool": state.current_address,
        "n_bars": len(master),
        "note": "constant_TVL_approx; hard_filters applied via decide_switch",
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache-dir", type=Path, default=ROOT / "data" / "r003_ohlcv")
    ap.add_argument("--out", type=Path, default=ROOT / "data" / "r003_grid_20260928.json")
    ap.add_argument("--top-n", type=int, default=5, help="OHLCV fetch for top-N by volume among SOL-USDC")
    args = ap.parse_args()

    now_ts = time.time()
    rows = fetch_true_sol_usdc()
    snaps = [snapshot_from_orca_row(r, source_ts=now_ts) for r in rows]
    ranked = filter_and_rank(snaps, now_ts=now_ts)
    # Research set: top-N by volume even if below TVL (flagged)
    by_vol = sorted(snaps, key=lambda p: p.volume_24h, reverse=True)[: args.top_n]

    meta: dict[str, dict[str, Any]] = {}
    for p in by_vol:
        ok, reason = True, "ok"
        from orca_tight_range.pool_rank import passes_hard_filters

        ok, reason = passes_hard_filters(p, now_ts=now_ts)
        meta[p.address] = {
            "address": p.address,
            "fee": p.fee_pct / 100.0,
            "tvl": p.tvl_usd,
            "label": f"{p.fee_pct:g}%",
            "passes_hard_filter": ok,
            "filter_reason": reason,
            "score": p.score,
        }

    series: dict[str, list[Candle]] = {}
    for addr, m in meta.items():
        cache = args.cache_dir / f"ohlcv_{addr[:8]}.json"
        if cache.exists():
            series[addr] = load_hourly_candles(cache)
            print(f"cache {addr[:12]} n={len(series[addr])}", flush=True)
            continue
        if addr.startswith("Czfq"):
            shared = ROOT / "data" / "solusdc_ohlcv_hourly.json"
            if shared.exists():
                series[addr] = load_hourly_candles(shared)
                print(f"shared Czfq n={len(series[addr])}", flush=True)
                continue
        try:
            print(f"fetch {addr[:12]} …", flush=True)
            candles = gecko_ohlcv(addr)
            save_ohlcv(addr, candles, cache)
            series[addr] = candles
            print(f"  bars={len(candles)}", flush=True)
            time.sleep(2.5)
        except (urllib.error.URLError, TimeoutError, KeyError, json.JSONDecodeError) as e:
            print(f"  FAIL {e}", flush=True)

    sit_rows: list[dict[str, Any]] = []
    for addr, m in meta.items():
        if addr not in series:
            sit_rows.append(
                asdict(
                    SitResult(
                        addr,
                        m["label"],
                        m["fee"],
                        m["tvl"],
                        "missing",
                        0,
                        0,
                        0,
                        0,
                        0,
                        m["passes_hard_filter"],
                        note="ohlcv_fetch_failed",
                    )
                )
            )
            continue
        for train, name in ((True, "train"), (False, "holdout")):
            bars = window_slice(series[addr], train=train)
            end_eq, end_hodl, fees = sit_wide(bars, fee=m["fee"], tvl=m["tvl"])
            note = "constant_TVL_approx"
            if not m["passes_hard_filter"]:
                note += f"; FAIL_FILTER:{m['filter_reason']}"
            sit_rows.append(
                asdict(
                    SitResult(
                        address=addr,
                        label=m["label"],
                        fee=m["fee"],
                        tvl=m["tvl"],
                        window=name,
                        end_equity=end_eq,
                        end_hodl=end_hodl,
                        fees=fees,
                        edge=end_eq - end_hodl,
                        n_bars=len(bars),
                        passes_hard_filter=m["passes_hard_filter"],
                        note=note,
                    )
                )
            )

    # Switcher only among pools that pass hard filters (may be Czfq-only)
    hard_meta = {a: m for a, m in meta.items() if m["passes_hard_filter"] and a in series}
    if not hard_meta:
        switch_train = {"error": "no_pool_passes_hard_filter"}
        switch_hold = {"error": "no_pool_passes_hard_filter"}
    else:
        hard_series = {a: series[a] for a in hard_meta}
        switch_train = switcher_replay(hard_series, hard_meta, train=True)
        switch_hold = switcher_replay(hard_series, hard_meta, train=False)

    payload = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "caveat": (
            "constant_TVL_approx. R002 pool_screen used tokens=SOL,USDC (OR) and "
            "mislabelled non-SOL-USDC pools as higher fee intensity. R003 uses "
            "tokensBothOf. Only pools with TVL>=500k are promotion-eligible."
        ),
        "min_tvl_usd": MIN_TVL_USD,
        "train_end": TRAIN_END_TS,
        "n_api_sol_usdc": len(snaps),
        "n_pass_hard_filter": len(ranked),
        "ranked_top": [
            {"address": p.address, "fee_pct": p.fee_pct, "tvl": p.tvl_usd, "score": p.score}
            for p in ranked[:10]
        ],
        "research_meta": meta,
        "sit_wide_16pct_1x": sit_rows,
        "switcher_train": switch_train,
        "switcher_holdout": switch_hold,
        "promotes_vs_czfq_holdout": [],  # none: no other hard-filter pool
        "n_series": {a[:12]: len(c) for a, c in series.items()},
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2))
    print(
        json.dumps(
            {
                "n_pass_hard_filter": payload["n_pass_hard_filter"],
                "ranked_top": payload["ranked_top"],
                "switcher_holdout": switch_hold,
                "n_series": payload["n_series"],
            },
            indent=2,
        )
    )
    print(f"wrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
