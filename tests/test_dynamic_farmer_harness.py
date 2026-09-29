"""Offline harness for dynamic_farmer.tick — no Hummingbot import."""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from orca_tight_range.dynamic_farmer import FarmerState, tick  # noqa: E402
from orca_tight_range.logic import Action  # noqa: E402
from orca_tight_range.pool_rank import PoolSnapshot  # noqa: E402

NOW = 1_725_000_000.0


def _p(addr: str, fee: float, vol24: float, vol7d: float) -> PoolSnapshot:
    return PoolSnapshot(
        address=addr,
        fee_pct=fee,
        tvl_usd=2_000_000,
        volume_24h=vol24,
        volume_7d=vol7d,
        created_at="2023-01-01T00:00:00Z",
    )


def test_initial_open_and_band():
    st = FarmerState(race_end_ts=NOW + 48 * 3600)
    pools = [
        _p("LOW", 0.04, 10_000_000, 70_000_000),
        _p("HOT", 0.16, 40_000_000, 200_000_000),
    ]
    t, st = tick(
        st,
        now_ts=NOW,
        spot=Decimal("150"),
        equity=Decimal("800"),
        momentum_sign=0,
        recent_returns=(),
        pools=pools,
        do_rank=True,
    )
    assert t.switch.action == "open"
    assert t.pool_address == "HOT"
    assert t.band.action == Action.OPEN
    assert st.position is not None
    assert t.score_table


def test_freeze_on_scan_error_keeps_pool():
    st = FarmerState(race_end_ts=NOW + 48 * 3600)
    pools = [_p("HOT", 0.16, 40_000_000, 200_000_000)]
    t, st = tick(
        st,
        now_ts=NOW,
        spot=Decimal("150"),
        equity=Decimal("800"),
        momentum_sign=0,
        recent_returns=(),
        pools=pools,
        do_rank=True,
    )
    assert st.ranker.current_address == "HOT"
    t2, st2 = tick(
        st,
        now_ts=NOW + 3600,
        spot=Decimal("151"),
        equity=Decimal("800"),
        momentum_sign=0,
        recent_returns=(),
        pools=None,
        scan_error="timeout",
        do_rank=True,
    )
    assert t2.frozen
    assert t2.switch.action == "freeze"
    assert st2.ranker.current_address == "HOT"
    # Band holds; does not close
    assert t2.band.action == Action.HOLD


def test_hysteresis_switch_clears_position():
    cur = _p("CUR", 0.04, 10_000_000, 70_000_000)
    hot = _p("HOT", 0.16, 50_000_000, 200_000_000)
    st = FarmerState(race_end_ts=NOW + 48 * 3600)
    t0, st = tick(
        st,
        now_ts=NOW,
        spot=Decimal("150"),
        equity=Decimal("800"),
        momentum_sign=0,
        recent_returns=(),
        pools=[cur],
        do_rank=True,
    )
    assert t0.pool_address == "CUR"
    assert st.position is not None
    # Two scans with HOT winning
    t1, st = tick(
        st,
        now_ts=NOW + 3600,
        spot=Decimal("150"),
        equity=Decimal("800"),
        momentum_sign=0,
        recent_returns=(),
        pools=[cur, hot],
        do_rank=True,
    )
    assert t1.switch.action == "hold"
    t2, st = tick(
        st,
        now_ts=NOW + 7200,
        spot=Decimal("150"),
        equity=Decimal("800"),
        momentum_sign=0,
        recent_returns=(),
        pools=[cur, hot],
        do_rank=True,
    )
    assert t2.switch.action == "switch"
    assert t2.pool_address == "HOT"
    # Position cleared so band re-opens on new pool
    assert t2.band.action == Action.OPEN


def test_subhourly_skips_rank():
    st = FarmerState(race_end_ts=NOW + 48 * 3600)
    pools = [_p("HOT", 0.16, 40_000_000, 200_000_000)]
    _, st = tick(
        st,
        now_ts=NOW,
        spot=Decimal("150"),
        equity=Decimal("800"),
        momentum_sign=0,
        recent_returns=(),
        pools=pools,
        do_rank=True,
    )
    t, st = tick(
        st,
        now_ts=NOW + 60,
        spot=Decimal("150.1"),
        equity=Decimal("800"),
        momentum_sign=0,
        recent_returns=(),
        pools=None,
        do_rank=False,
    )
    assert t.switch.reason == "rank_skipped"
    assert t.pool_address == "HOT"
