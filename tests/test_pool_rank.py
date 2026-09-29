"""Unit tests for pool_rank (no network)."""

from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orca_tight_range.pool_rank import (  # noqa: E402
    PoolSnapshot,
    RankerState,
    decide_switch,
    expected_gain_usd,
    filter_and_rank,
    passes_hard_filters,
    switch_cost_usd,
)


NOW = 1_725_000_000.0  # ~2024-08-30 UTC


def _pool(
    addr: str,
    *,
    fee_pct: float = 0.16,
    tvl: float = 2_000_000,
    vol24: float = 20_000_000,
    vol7d: float = 100_000_000,
    warning: bool = False,
    created: str | None = "2023-01-01T00:00:00Z",
) -> PoolSnapshot:
    return PoolSnapshot(
        address=addr,
        fee_pct=fee_pct,
        tvl_usd=tvl,
        volume_24h=vol24,
        volume_7d=vol7d,
        has_warning=warning,
        created_at=created,
    )


def test_filters_reject_warning_thin_tvl_high_fee():
    ok, _ = passes_hard_filters(_pool("A"), now_ts=NOW)
    assert ok
    bad_w, reason = passes_hard_filters(_pool("B", warning=True), now_ts=NOW)
    assert not bad_w and "hasWarning" in reason
    bad_t, reason = passes_hard_filters(_pool("C", tvl=100_000), now_ts=NOW)
    assert not bad_t and "tvl" in reason
    bad_f, reason = passes_hard_filters(_pool("D", fee_pct=2.0), now_ts=NOW)
    assert not bad_f and "fee_pct" in reason


def test_score_is_min_of_24h_and_7d():
    # Spike 24h, quiet 7d -> score capped by 7d
    p = _pool("X", vol24=100_000_000, vol7d=14_000_000)  # 7d daily = 2M
    assert p.intensity_24h > p.intensity_7d
    assert p.score == p.intensity_7d


def test_rank_orders_by_score():
    low = _pool("LOW", fee_pct=0.04, vol24=10_000_000, vol7d=70_000_000)
    high = _pool("HIGH", fee_pct=0.16, vol24=28_000_000, vol7d=140_000_000)
    ranked = filter_and_rank([low, high], now_ts=NOW)
    assert ranked[0].address == "HIGH"


def test_initial_open_takes_top():
    pools = [_pool("A", fee_pct=0.04), _pool("B", fee_pct=0.16, vol24=30_000_000)]
    d, st = decide_switch(pools, RankerState(), now_ts=NOW, equity=800, hours_left=48)
    assert d.action == "open"
    assert d.target_address == "B"
    assert st.current_address == "B"


def test_hysteresis_requires_two_scans():
    current = _pool("CUR", fee_pct=0.04, vol24=10_000_000, vol7d=70_000_000)
    hot = _pool("HOT", fee_pct=0.16, vol24=50_000_000, vol7d=200_000_000)
    state = RankerState(current_address="CUR")
    d1, st1 = decide_switch([current, hot], state, now_ts=NOW, equity=800, hours_left=48)
    assert d1.action == "hold"
    assert "pending_streak=1" in d1.reason
    d2, st2 = decide_switch([current, hot], st1, now_ts=NOW + 3600, equity=800, hours_left=47)
    assert d2.action == "switch"
    assert d2.target_address == "HOT"
    assert st2.current_address == "HOT"


def test_cost_gate_blocks_tiny_gain():
    # Barely clears 1.5x but hours_left tiny so gain < cost
    current = _pool("CUR", fee_pct=0.04, vol24=10_000_000, vol7d=70_000_000)
    hot = _pool("HOT", fee_pct=0.16, vol24=50_000_000, vol7d=200_000_000)
    state = RankerState(current_address="CUR", pending_address="HOT", pending_streak=1)
    d, _ = decide_switch(
        [current, hot], state, now_ts=NOW, equity=800, hours_left=0.1
    )
    assert d.action == "hold"
    assert "cost_gate" in d.reason


def test_switch_cap():
    current = _pool("CUR", fee_pct=0.04, vol24=10_000_000, vol7d=70_000_000)
    hot = _pool("HOT", fee_pct=0.16, vol24=50_000_000, vol7d=200_000_000)
    stamps = [NOW - 1000, NOW - 2000, NOW - 3000]
    state = RankerState(
        current_address="CUR",
        pending_address="HOT",
        pending_streak=1,
        switch_timestamps=stamps,
    )
    d, _ = decide_switch([current, hot], state, now_ts=NOW, equity=800, hours_left=48)
    assert d.action == "hold"
    assert "switch_cap" in d.reason


def test_scan_error_freezes():
    state = RankerState(current_address="CUR")
    d, st = decide_switch(
        None, state, now_ts=NOW, equity=800, hours_left=48, scan_error="timeout"
    )
    assert d.action == "freeze"
    assert st.frozen is True


def test_switch_cost_formula():
    assert switch_cost_usd(800) == 2.0 + 0.8
    assert expected_gain_usd(0.02, 0.01, 800, 24) == 8.0
