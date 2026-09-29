"""Unit tests for ml_intensity shadow ranker (no network)."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orca_tight_range.ml_intensity import (  # noqa: E402
    build_examples,
    walk_forward_pick,
)


def _row(ts: float, pools: list[dict]) -> dict:
    ranked = sorted(pools, key=lambda p: p["score"], reverse=True)
    return {
        "ts_unix": ts,
        "top": [
            {"address": ranked[0]["address"], "score": ranked[0]["score"]}
        ]
        if ranked
        else [],
        "pools": pools,
    }


def test_insufficient_examples_no_promote(tmp_path: Path):
    rows = [
        _row(
            1000.0 + i * 3600,
            [
                {
                    "address": "A",
                    "int24": 0.01,
                    "int7d": 0.01,
                    "score": 0.01,
                    "vol24": 1e6,
                    "tvl": 1e6,
                    "price": 150,
                }
            ],
        )
        for i in range(5)
    ]
    pick = walk_forward_pick(rows, min_train=24)
    assert pick.promote_ready is False
    assert "insufficient" in pick.note


def test_build_examples_pairs_24h():
    rows = []
    for i in range(30):
        score_a = 0.01 + 0.0001 * i
        score_b = 0.02 - 0.00005 * i
        rows.append(
            _row(
                1_000_000 + i * 3600,
                [
                    {
                        "address": "A",
                        "int24": score_a,
                        "int7d": score_a,
                        "score": score_a,
                        "vol24": 1e6 + i * 1e4,
                        "tvl": 2e6,
                        "price": 150 + i * 0.1,
                    },
                    {
                        "address": "B",
                        "int24": score_b,
                        "int7d": score_b,
                        "score": score_b,
                        "vol24": 2e6,
                        "tvl": 2e6,
                        "price": 150,
                    },
                ],
            )
        )
    ex = build_examples(rows)
    assert len(ex) > 10
    pick = walk_forward_pick(rows, min_train=10)
    assert pick.rule_address in ("A", "B")
    # ml may or may not promote; just ensure it returns an address or note
    assert pick.note
