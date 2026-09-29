"""Ridge next-24h intensity ranker — shadow only until holdout beats the rule.

Features per pool at scan t: [int_24h, int_7d, int_30d_proxy, vol_delta_24h,
tvl_delta, price_delta]. Target: intensity over the next 24h (approx from
later snapshot score). Walk-forward on the snapshot JSONL.

With <48h of snapshots before race day this stays a shadow logger.
Promote to acting only if it beats min(24h,7d) on held-out snapshot days.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional, Sequence


@dataclass(frozen=True)
class ShadowPick:
    rule_address: Optional[str]
    ml_address: Optional[str]
    rule_score: float
    ml_predicted: float
    promote_ready: bool
    note: str


def _ridge_fit(X: list[list[float]], y: list[float], l2: float = 1.0) -> list[float]:
    """Closed-form ridge with intercept column. Pure Python, no numpy."""
    if not X or not y or len(X) != len(y):
        return []
    n = len(X)
    d = len(X[0]) + 1  # + intercept
    # Build X'X and X'y
    xtx = [[0.0] * d for _ in range(d)]
    xty = [0.0] * d
    for i in range(n):
        row = [1.0] + X[i]
        for a in range(d):
            xty[a] += row[a] * y[i]
            for b in range(d):
                xtx[a][b] += row[a] * row[b]
    for a in range(1, d):  # leave intercept unpenalized
        xtx[a][a] += l2
    return _solve(xtx, xty)


def _solve(a: list[list[float]], b: list[float]) -> list[float]:
    """Gaussian elimination with partial pivot."""
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for col in range(n):
        pivot = max(range(col, n), key=lambda r: abs(m[r][col]))
        if abs(m[pivot][col]) < 1e-12:
            return []
        m[col], m[pivot] = m[pivot], m[col]
        div = m[col][col]
        for j in range(col, n + 1):
            m[col][j] /= div
        for r in range(n):
            if r == col:
                continue
            factor = m[r][col]
            for j in range(col, n + 1):
                m[r][j] -= factor * m[col][j]
    return [m[i][n] for i in range(n)]


def _predict(w: Sequence[float], x: Sequence[float]) -> float:
    if not w:
        return 0.0
    return w[0] + sum(w[i + 1] * x[i] for i in range(len(x)))


def load_snapshot_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def _pool_map(row: dict[str, Any]) -> dict[str, dict[str, Any]]:
    out = {}
    for p in row.get("pools") or []:
        addr = p.get("address")
        if addr:
            out[addr] = p
    return out


def build_examples(
    rows: Sequence[dict[str, Any]],
    *,
    horizon_hours: float = 24.0,
) -> list[tuple[list[float], float, str, float]]:
    """Return (features, target_score, address, ts) examples."""
    if len(rows) < 3:
        return []
    indexed = sorted(rows, key=lambda r: float(r.get("ts_unix") or 0))
    examples: list[tuple[list[float], float, str, float]] = []
    for i, row in enumerate(indexed):
        ts = float(row.get("ts_unix") or 0)
        pm = _pool_map(row)
        # Find a later row ~24h ahead
        target_row = None
        for j in range(i + 1, len(indexed)):
            dt_h = (float(indexed[j].get("ts_unix") or 0) - ts) / 3600.0
            if dt_h >= horizon_hours * 0.8:
                target_row = indexed[j]
                if dt_h <= horizon_hours * 1.5:
                    break
        if target_row is None:
            continue
        tm = _pool_map(target_row)
        prev = _pool_map(indexed[i - 1]) if i > 0 else {}
        for addr, p in pm.items():
            if addr not in tm:
                continue
            int24 = float(p.get("int24") or 0)
            int7d = float(p.get("int7d") or 0)
            score = float(p.get("score") or min(int24, int7d))
            # 30d proxy: blend 7d toward score (no true 30d in API yet)
            int30 = 0.5 * int7d + 0.5 * score
            prev_p = prev.get(addr) or {}
            vol_delta = float(p.get("vol24") or 0) - float(prev_p.get("vol24") or p.get("vol24") or 0)
            tvl_delta = float(p.get("tvl") or 0) - float(prev_p.get("tvl") or p.get("tvl") or 0)
            price_delta = float(p.get("price") or 0) - float(prev_p.get("price") or p.get("price") or 0)
            # Scale deltas
            feats = [
                int24,
                int7d,
                int30,
                vol_delta / 1e6,
                tvl_delta / 1e6,
                price_delta,
            ]
            tgt = float(tm[addr].get("score") or 0)
            examples.append((feats, tgt, addr, ts))
    return examples


def walk_forward_pick(
    rows: Sequence[dict[str, Any]],
    *,
    min_train: int = 24,
) -> ShadowPick:
    """Train on all but last day of examples; pick ML top on latest scan."""
    examples = build_examples(list(rows))
    if len(examples) < min_train:
        latest_top = None
        latest_score = 0.0
        if rows:
            top = (sorted(rows, key=lambda r: float(r.get("ts_unix") or 0))[-1].get("top") or [{}])
            if top:
                latest_top = top[0].get("address")
                latest_score = float(top[0].get("score") or 0)
        return ShadowPick(
            rule_address=latest_top,
            ml_address=None,
            rule_score=latest_score,
            ml_predicted=0.0,
            promote_ready=False,
            note=f"insufficient_examples n={len(examples)} need>={min_train}",
        )

    # Hold out last ~24 examples for promote check
    hold_n = max(6, len(examples) // 5)
    train, hold = examples[:-hold_n], examples[-hold_n:]
    X = [e[0] for e in train]
    y = [e[1] for e in train]
    w = _ridge_fit(X, y)
    if not w:
        return ShadowPick(None, None, 0.0, 0.0, False, "ridge_fit_failed")

    # Rule = min score on hold addresses at their feature time — compare MAE
    rule_err = 0.0
    ml_err = 0.0
    for feats, tgt, _addr, _ts in hold:
        pred = _predict(w, feats)
        rule_proxy = min(feats[0], feats[1])  # int24, int7d
        rule_err += abs(rule_proxy - tgt)
        ml_err += abs(pred - tgt)
    rule_mae = rule_err / len(hold)
    ml_mae = ml_err / len(hold)
    promote = ml_mae + 1e-12 < rule_mae

    # Latest scan: score each pool with ML, pick argmax
    latest = sorted(rows, key=lambda r: float(r.get("ts_unix") or 0))[-1]
    rule_addr = None
    rule_score = 0.0
    top = latest.get("top") or []
    if top:
        rule_addr = top[0].get("address")
        rule_score = float(top[0].get("score") or 0)

    pm = _pool_map(latest)
    prev_rows = sorted(rows, key=lambda r: float(r.get("ts_unix") or 0))
    prev = _pool_map(prev_rows[-2]) if len(prev_rows) > 1 else {}
    best_addr = None
    best_pred = -math.inf
    for addr, p in pm.items():
        int24 = float(p.get("int24") or 0)
        int7d = float(p.get("int7d") or 0)
        score = float(p.get("score") or min(int24, int7d))
        int30 = 0.5 * int7d + 0.5 * score
        prev_p = prev.get(addr) or {}
        feats = [
            int24,
            int7d,
            int30,
            (float(p.get("vol24") or 0) - float(prev_p.get("vol24") or p.get("vol24") or 0)) / 1e6,
            (float(p.get("tvl") or 0) - float(prev_p.get("tvl") or p.get("tvl") or 0)) / 1e6,
            float(p.get("price") or 0) - float(prev_p.get("price") or p.get("price") or 0),
        ]
        pred = _predict(w, feats)
        if pred > best_pred:
            best_pred = pred
            best_addr = addr

    return ShadowPick(
        rule_address=rule_addr,
        ml_address=best_addr,
        rule_score=rule_score,
        ml_predicted=best_pred if best_addr else 0.0,
        promote_ready=promote,
        note=f"ml_mae={ml_mae:.6f} rule_mae={rule_mae:.6f} n_train={len(train)} n_hold={len(hold)}",
    )


def shadow_from_log(path: Path) -> ShadowPick:
    return walk_forward_pick(load_snapshot_rows(path))
